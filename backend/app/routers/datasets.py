"""Dataset upload endpoint (MLE-F-006).

Accepts a CSV upload, validates that it can be parsed, persists the raw bytes
through the shared dataset store and returns the generated dataset ID together
with the column names, a preview of the first rows and any data-quality
warnings.
"""

import csv
import json
from io import BytesIO, TextIOWrapper
from pathlib import PureWindowsPath

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..deps import get_optional_user
from ..models import User
from ..services.dataset_store import store_dataset

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
)

# Number of rows returned in the upload preview.
PREVIEW_ROWS = 5
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_COLUMNS = 1024
MAX_LINE_BYTES = 128 * 1024

# Rejected encodings/parse failures all surface as a 400 with this message.
PARSE_ERROR = "Unable to parse the uploaded CSV file."


def _parse_csv(content: bytes) -> pd.DataFrame:
    """Parse uploaded CSV bytes into a DataFrame or raise ``ValueError``.

    ``utf-8-sig`` transparently strips a leading BOM while pandas' C parser
    handles quoted delimiters and CRLF line endings.
    """

    if not content.strip():
        raise ValueError("Uploaded CSV file is empty.")

    if b"\x00" in content or content.startswith((b"%PDF-", b"PK\x03\x04", b"\x89PNG")):
        raise HTTPException(415, "Expected a UTF-8 CSV file.")
    if any(len(line) > MAX_LINE_BYTES for line in BytesIO(content)):
        raise ValueError("CSV line exceeds 128 KiB.")

    try:
        with TextIOWrapper(BytesIO(content), encoding="utf-8-sig", newline="") as stream:
            header = None
            for row in csv.reader(stream, strict=True):
                if not row:
                    continue
                if len(row) > MAX_COLUMNS:
                    raise ValueError("CSV exceeds 1024 columns.")
                if header is None:
                    header = row
                    if len(set(header)) != len(header):
                        raise ValueError("CSV column names must be unique.")
                elif len(row) != len(header):
                    raise ValueError("CSV rows must match the number of columns in the header.")
    except UnicodeDecodeError as exc:
        raise HTTPException(415, "Expected a UTF-8 CSV file.") from exc
    except csv.Error as exc:
        raise ValueError(PARSE_ERROR) from exc

    try:
        dataframe = pd.read_csv(BytesIO(content), encoding="utf-8-sig")
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
        ValueError,
    ) as exc:
        raise ValueError(PARSE_ERROR) from exc

    if dataframe.empty:
        raise ValueError("CSV file contains no data rows.")

    return dataframe


def _build_preview(dataframe: pd.DataFrame) -> list[dict]:
    """Return the first ``PREVIEW_ROWS`` rows in JSON-safe form.

    Round-tripping through ``to_json`` converts NaN to ``null``, numpy scalars
    to native JSON types and timestamps to ISO strings so the payload is safe
    to serialize and render in the frontend preview table.
    """

    preview = dataframe.head(PREVIEW_ROWS)
    return json.loads(preview.to_json(orient="records", date_format="iso"))


def _build_warnings(dataframe: pd.DataFrame) -> list[str]:
    """Report columns that contain missing values."""

    warnings = []

    for column, count in dataframe.isna().sum().items():
        if count > 0:
            warnings.append(f"Column '{column}' contains {count} missing value(s).")

    return warnings


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    user: User | None = Depends(get_optional_user),
):
    """Accept a CSV upload and return dataset metadata plus a preview."""

    try:
        name = PureWindowsPath(file.filename or "").name
        if not name.lower().endswith(".csv") or not name.isprintable():
            raise HTTPException(415, "Choose a file with a .csv extension.")
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "CSV exceeds the 10 MiB limit.")
    finally:
        await file.close()

    try:
        dataframe = _parse_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    dataset_id = store_dataset(
        content=content,
        name=name,
        owner_id=user.user_id if user else None,
    )

    return {
        "dataset_id": dataset_id,
        "columns": [str(column) for column in dataframe.columns],
        "preview": _build_preview(dataframe),
        "warnings": _build_warnings(dataframe),
    }
