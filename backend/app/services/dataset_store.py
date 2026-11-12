"""Dataset storage adapter for the upload module and evaluation engine.

Member 2's upload route should call store_dataset(content, original_name, owner_id)
and return the generated dataset_id.
"""
import io
import json
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from ..ml.errors import EvaluationError

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _dir() -> Path:
    path = Path(os.getenv("DATASET_DIR", "./uploads"))
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class LoadedDataset:
    dataset_id: str
    name: str
    df: pd.DataFrame


def store_dataset(content: bytes, name: str, owner_id: Optional[int]) -> str:
    dataset_id = "ds_" + uuid.uuid4().hex
    base = _dir()
    (base / f"{dataset_id}.csv").write_bytes(content)
    (base / f"{dataset_id}.meta.json").write_text(json.dumps({"name": name, "owner_id": owner_id}), encoding="utf-8")
    return dataset_id


def load_dataset(dataset_id: str, requester_id: Optional[int]) -> LoadedDataset:
    not_found = EvaluationError("DATASET_NOT_FOUND", "Dataset not found", 404)
    if not _ID_RE.fullmatch(dataset_id):
        raise not_found
    base = _dir()
    csv_path, meta_path = base / f"{dataset_id}.csv", base / f"{dataset_id}.meta.json"
    if not csv_path.is_file():
        raise not_found
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    except (ValueError, OSError):
        meta = {}
    owner = meta.get("owner_id")
    if owner is not None and owner != requester_id:
        raise not_found
    try:
        frame = pd.read_csv(io.BytesIO(csv_path.read_bytes()), encoding="utf-8-sig")
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError, OSError):
        raise EvaluationError("INVALID_DATASET", "The stored dataset is not a valid CSV file", 422)
    return LoadedDataset(dataset_id=dataset_id, name=meta.get("name") or f"{dataset_id}.csv", df=frame)
