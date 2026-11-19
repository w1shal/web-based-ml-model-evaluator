"""API contract tests for the dataset upload endpoint (MLE-F-006, TC-006, TC-009c)."""

import pytest


@pytest.fixture
def dataset_dir(tmp_path, monkeypatch):
    """Point the dataset store at an isolated directory for the test."""

    directory = tmp_path / "datasets"
    directory.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DATASET_DIR", str(directory))
    return directory


def upload_csv(client, content: bytes, filename="data.csv", headers=None):
    return client.post(
        "/datasets/upload",
        files={"file": (filename, content, "text/csv")},
        headers=headers,
    )


@pytest.mark.integration
def test_valid_csv_upload_returns_metadata_and_preview(client, dataset_dir):   # TC-006
    csv_content = b"name,age,score\nAlice,22,90\nBob,24,85\n"

    response = upload_csv(client, csv_content, "students.csv")

    assert response.status_code == 200, response.text
    body = response.json()

    assert set(body) == {"dataset_id", "columns", "preview", "warnings"}
    assert body["dataset_id"].startswith("ds_")
    assert body["columns"] == ["name", "age", "score"]

    assert len(body["preview"]) == 2
    assert body["preview"][0] == {"name": "Alice", "age": 22, "score": 90}
    assert body["preview"][1] == {"name": "Bob", "age": 24, "score": 85}

    assert body["warnings"] == []

    # The raw bytes and metadata are persisted under the returned ID.
    assert (dataset_dir / f"{body['dataset_id']}.csv").read_bytes() == csv_content
    assert (dataset_dir / f"{body['dataset_id']}.meta.json").exists()


@pytest.mark.integration
def test_utf8_bom_is_stripped_from_column_names(client, dataset_dir):          # TC-006
    csv_content = "\ufeffname,age\nAlice,22\nBob,24\n".encode("utf-8")

    body = upload_csv(client, csv_content, "bom.csv").json()

    assert body["columns"] == ["name", "age"]
    assert body["preview"][0]["name"] == "Alice"


@pytest.mark.integration
def test_quoted_commas_are_parsed_as_single_fields(client, dataset_dir):       # TC-006
    csv_content = (
        b"name,description,score\n"
        b'Alice,"Machine learning, Python",90\n'
        b'Bob,"Statistics, Data Science",85\n'
    )

    body = upload_csv(client, csv_content, "quoted.csv").json()

    assert body["columns"] == ["name", "description", "score"]
    assert body["preview"][0]["description"] == "Machine learning, Python"
    assert body["preview"][1]["description"] == "Statistics, Data Science"


@pytest.mark.integration
def test_crlf_line_endings_are_parsed(client, dataset_dir):                    # TC-006
    csv_content = b"name,age,score\r\nAlice,22,90\r\nBob,24,85\r\n"

    body = upload_csv(client, csv_content, "crlf.csv").json()

    assert body["columns"] == ["name", "age", "score"]
    assert len(body["preview"]) == 2
    assert body["preview"][0]["name"] == "Alice"
    assert body["preview"][1]["name"] == "Bob"


@pytest.mark.integration
def test_preview_is_limited_to_first_five_rows(client, dataset_dir):           # TC-009c
    rows = "".join(f"{index},value-{index}\n" for index in range(1, 8))
    csv_content = ("id,label\n" + rows).encode("utf-8")

    body = upload_csv(client, csv_content, "preview.csv").json()

    assert len(body["preview"]) == 5
    assert body["preview"][0]["id"] == 1
    assert body["preview"][4]["id"] == 5


@pytest.mark.integration
def test_missing_values_are_reported_as_warnings(client, dataset_dir):         # TC-009c
    csv_content = b"name,age,score\nAlice,,90\nBob,24,\nCharlie,25,95\n"

    body = upload_csv(client, csv_content, "missing.csv").json()

    assert len(body["warnings"]) == 2
    assert any("age" in warning and "1" in warning for warning in body["warnings"])
    assert any("score" in warning and "1" in warning for warning in body["warnings"])

    # Missing cells stay JSON-safe (null) in the preview.
    assert body["preview"][0]["age"] is None
    assert body["preview"][1]["score"] is None


@pytest.mark.integration
def test_dataset_ids_are_unique(client, dataset_dir):
    csv_content = b"name,age\nAlice,22\n"

    first = upload_csv(client, csv_content, "first.csv").json()["dataset_id"]
    second = upload_csv(client, csv_content, "second.csv").json()["dataset_id"]

    assert first != second


@pytest.mark.integration
def test_guest_can_upload_without_authentication(client, dataset_dir):
    body = upload_csv(client, b"name,age\nAlice,22\n", "guest.csv").json()

    assert body["dataset_id"].startswith("ds_")
    assert body["columns"] == ["name", "age"]


@pytest.mark.integration
def test_authenticated_upload_records_owner(client, make_user, dataset_dir):
    user = make_user("csvuser")

    body = upload_csv(
        client,
        b"name,age\nAlice,22\n",
        "authenticated.csv",
        headers=user["headers"],
    ).json()

    metadata = (dataset_dir / f"{body['dataset_id']}.meta.json").read_text(encoding="utf-8")
    assert str(user["user_id"]) in metadata


@pytest.mark.integration
def test_invalid_token_is_rejected(client, dataset_dir):
    response = upload_csv(
        client,
        b"name,age\nAlice,22\n",
        headers={"Authorization": "Bearer not.a.token"},
    )

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.parametrize(
    "content",
    [
        pytest.param(b"", id="empty-file"),
        pytest.param(b"   \n", id="whitespace-only"),
        pytest.param(b"name,age\n", id="header-only"),
    ],
)
def test_invalid_csv_returns_400(client, dataset_dir, content):
    response = upload_csv(client, content, "invalid.csv")

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.integration
def test_missing_file_returns_400(client):
    response = client.post("/datasets/upload")

    assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.parametrize("name,content,status", [
    ("wrong.txt", b"a,b\n1,2", 415),
    ("binary.csv", b"a,b\n1,\x00", 415),
    ("document.csv", b"%PDF-1.7\nexample", 415),
    ("oversize.csv", b"x" * (10 * 1024 * 1024 + 1), 413),
    ("wide.csv", b"a," * 1024 + b"b\n", 400),
    ("long.csv", b"a,b\n1," + b"x" * 131072, 400),
], ids=["extension", "binary", "document", "size", "width", "line"])
def test_rejected_upload_leaves_no_dataset(client, dataset_dir, name, content, status):
    assert upload_csv(client, content, name).status_code == status
    assert list(dataset_dir.iterdir()) == []


@pytest.mark.integration
def test_error_correlation_and_log_privacy(client, caplog):
    import logging

    with caplog.at_level(logging.INFO, logger="app.requests"):
        response = upload_csv(client, b"private-dataset-sentinel", "wrong.txt")
    error = response.json()["error"]
    assert error["request_id"] == response.headers["X-Request-ID"]
    assert error["request_id"] in caplog.text
    assert "private-dataset-sentinel" not in caplog.text
