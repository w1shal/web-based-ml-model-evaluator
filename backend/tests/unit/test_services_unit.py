"""Unit tests for services, rate limiting and report helpers."""

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pandas as pd
import pytest
from starlette.requests import Request

from app import ratelimit
from app.ml.errors import EvaluationError
from app.ml.gate import GateTimeout
from app.ratelimit import SlidingWindowLimiter, _positive_int_env, client_ip
from app.routers.reports import _filename, _metric_text, _spreadsheet_safe, _timestamp
from app.schemas_evaluation import EvaluationRequest
from app.services import dataset_store, evaluation_service
from app.services.evaluation_service import _from_history_row, _to_history_row

# ------------------------------------------------------------ rate limiting


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_limiter_blocks_after_limit_and_recovers_after_window():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(clock)
    assert limiter.hit("k", 2, 10) == (True, 0)
    assert limiter.hit("k", 2, 10) == (True, 0)
    clock.now += 3
    assert limiter.hit("k", 2, 10) == (False, 7)
    assert limiter.hit("other", 2, 10) == (True, 0)  # keys are independent
    clock.now += 7
    assert limiter.hit("k", 2, 10) == (True, 0)


def test_limiter_retry_after_is_at_least_one_second():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(clock)
    limiter.hit("k", 1, 10)
    clock.now += 9.99
    assert limiter.hit("k", 1, 10) == (False, 1)


@pytest.mark.parametrize(("limit", "window"), [(0, 10), (1, 0), (-1, -1)])
def test_limiter_rejects_non_positive_settings(limit, window):
    with pytest.raises(ValueError):
        SlidingWindowLimiter().hit("k", limit, window)


def test_limiter_reset_clears_hits_and_clock():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(clock)
    limiter.hit("k", 1, 10)
    limiter.reset()
    assert limiter.clock is not clock
    assert limiter.hit("k", 1, 10) == (True, 0)


def test_positive_int_env(monkeypatch):
    monkeypatch.delenv("X_LIMIT", raising=False)
    assert _positive_int_env("X_LIMIT", 5) == 5
    monkeypatch.setenv("X_LIMIT", "12")
    assert _positive_int_env("X_LIMIT", 5) == 12
    for bad in ("abc", "0", "-3"):
        monkeypatch.setenv("X_LIMIT", bad)
        with pytest.raises(RuntimeError, match="positive integer"):
            _positive_int_env("X_LIMIT", 5)


def _request(headers=None, client=("10.0.0.1", 1234)):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": client,
    }
    return Request(scope)


def test_client_ip_ignores_forwarded_header_without_trust_proxy(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY", raising=False)
    assert client_ip(_request({"X-Forwarded-For": "1.2.3.4"})) == "10.0.0.1"


def test_client_ip_uses_first_forwarded_address_with_trust_proxy(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "1")
    assert client_ip(_request({"X-Forwarded-For": " 1.2.3.4 , 5.6.7.8"})) == "1.2.3.4"
    assert client_ip(_request({"X-Forwarded-For": " , 5.6.7.8"})) == "10.0.0.1"
    assert client_ip(_request()) == "10.0.0.1"


def test_client_ip_without_client_is_unknown(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY", raising=False)
    assert client_ip(_request(client=None)) == "unknown"


def test_rate_limit_dependency_raises_429_with_retry_after(monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setenv("RATE_LIMIT_DEMO_MAX", "1")
    dependency = ratelimit.rate_limit("demo", 5)
    dependency(_request())
    with pytest.raises(HTTPException) as error:
        dependency(_request())
    assert error.value.status_code == 429
    assert int(error.value.headers["Retry-After"]) >= 1


# ------------------------------------------------------------ dataset store


@pytest.fixture
def dataset_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATASET_DIR", str(tmp_path / "store"))
    return tmp_path / "store"


def test_store_and_load_dataset_roundtrip(dataset_dir):
    dataset_id = dataset_store.store_dataset(b"a,b\n1,2\n3,4\n", "tiny.csv", owner_id=5)
    assert dataset_id.startswith("ds_")
    assert json.loads((dataset_dir / f"{dataset_id}.meta.json").read_text()) == {"name": "tiny.csv", "owner_id": 5}
    loaded = dataset_store.load_dataset(dataset_id, requester_id=5)
    assert loaded.name == "tiny.csv"
    assert loaded.df.to_dict("list") == {"a": [1, 3], "b": [2, 4]}


def test_load_dataset_strips_utf8_bom(dataset_dir):
    dataset_id = dataset_store.store_dataset("﻿a,b\n1,2\n".encode(), "bom.csv", None)
    assert list(dataset_store.load_dataset(dataset_id, None).df.columns) == ["a", "b"]


@pytest.mark.parametrize("bad_id", ["", "../etc/passwd", "a" * 65, "id with space"])
def test_load_dataset_rejects_malformed_ids(dataset_dir, bad_id):
    with pytest.raises(EvaluationError) as error:
        dataset_store.load_dataset(bad_id, None)
    assert error.value.status_code == 404


def test_load_dataset_hides_other_owners_data(dataset_dir):
    dataset_id = dataset_store.store_dataset(b"a\n1\n", "x.csv", owner_id=1)
    for requester in (2, None):
        with pytest.raises(EvaluationError) as error:
            dataset_store.load_dataset(dataset_id, requester)
        assert error.value.code == "DATASET_NOT_FOUND"


def test_load_dataset_with_corrupt_or_missing_metadata(dataset_dir):
    dataset_id = dataset_store.store_dataset(b"a\n1\n", "x.csv", owner_id=1)
    (dataset_dir / f"{dataset_id}.meta.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(EvaluationError) as error:
        dataset_store.load_dataset(dataset_id, None)
    assert error.value.status_code == 404

    (dataset_dir / f"{dataset_id}.meta.json").unlink()
    with pytest.raises(EvaluationError) as error:
        dataset_store.load_dataset(dataset_id, 99)
    assert error.value.status_code == 404


def test_load_dataset_rejects_invalid_csv(dataset_dir):
    dataset_id = dataset_store.store_dataset(b"\xff\xfe\x00bad", "bad.csv", None)
    with pytest.raises(EvaluationError) as error:
        dataset_store.load_dataset(dataset_id, None)
    assert (error.value.code, error.value.status_code) == ("INVALID_DATASET", 422)


# ------------------------------------------------------ evaluation service


def test_history_row_roundtrip_preserves_metadata():
    result = {
        "algorithm": "knn", "name": "KNN", "status": "completed", "accuracy": 0.9,
        "precision": 0.8, "recall": 0.7, "f1_score": 0.75, "roc_auc": None,
        "confusion_matrix": [[1, 0], [0, 1]], "classes": ["a", "b"], "duration_ms": 3,
    }
    row = _to_history_row(result, {"dataset": {"rows": 10}})
    assert row["serialized_metrics"]["class_labels"] == ["a", "b"]
    assert row["serialized_metrics"]["run_info"] == {"dataset": {"rows": 10}}

    stored = SimpleNamespace(algorithm_name="knn", serialized_metrics=row["serialized_metrics"],
                             **{key: row[key] for key in evaluation_service._DONE_KEYS})
    restored = _from_history_row(stored)
    assert restored["classes"] == ["a", "b"]
    assert "run_info" not in restored and "class_labels" not in restored
    assert restored["accuracy"] == 0.9


def test_from_history_row_failed_result_has_no_metrics():
    stored = SimpleNamespace(algorithm_name="svm", serialized_metrics={"status": "failed", "error": "x"},
                             accuracy=None, precision=None, recall=None, f1_score=None,
                             roc_auc=None, confusion_matrix=None)
    assert _from_history_row(stored) == {"algorithm": "svm", "status": "failed", "error": "x"}


def test_from_history_row_without_serialized_metrics():
    stored = SimpleNamespace(algorithm_name="svm", serialized_metrics=None, accuracy=0.5, precision=0.5,
                             recall=0.5, f1_score=0.5, roc_auc=0.5, confusion_matrix=[[1]])
    assert _from_history_row(stored)["accuracy"] == 0.5


def test_get_evaluation_access_rules(session_factory, make_run):
    with session_factory() as db:
        with pytest.raises(EvaluationError) as error:
            evaluation_service.get_evaluation(db, "run_missing", None)
        assert error.value.status_code == 404

        guest_run = make_run(None)
        assert evaluation_service.get_evaluation(db, guest_run, None)["run_id"] == guest_run

        owned_run = make_run(1)
        with pytest.raises(EvaluationError) as error:
            evaluation_service.get_evaluation(db, owned_run, None)
        assert error.value.status_code == 401
        with pytest.raises(EvaluationError) as error:
            evaluation_service.get_evaluation(db, owned_run, 2)
        assert error.value.status_code == 403
        assert evaluation_service.get_evaluation(db, owned_run, 1)["status"] == "completed"


def test_execute_evaluation_maps_gate_timeout_to_server_busy(monkeypatch, dataset_dir):
    frame = pd.DataFrame({"x": range(20), "y": [0, 1] * 10})
    dataset_id = dataset_store.store_dataset(frame.to_csv(index=False).encode(), "d.csv", None)

    class BusyGate:
        def slot(self):
            raise GateTimeout()

    monkeypatch.setattr(evaluation_service, "evaluation_gate", BusyGate())
    request = EvaluationRequest(dataset_id=dataset_id, target_column="y", feature_columns=["x"], algorithms=["knn"])
    with pytest.raises(EvaluationError) as error:
        evaluation_service.execute_evaluation(SimpleNamespace(rollback=lambda: None), None, request)
    assert (error.value.code, error.value.status_code) == ("SERVER_BUSY", 503)


# ----------------------------------------------------------- report helpers


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ""),
        (0.5, 0.5),
        (3, 3),
        (True, "True"),
        ("plain", "plain"),
        ("=HYPERLINK(1)", "'=HYPERLINK(1)"),
        ("+1", "'+1"),
        ("-1", "'-1"),
        ("@SUM(A1)", "'@SUM(A1)"),
        ("  =cmd", "'  =cmd"),
        ("\t=cmd", "'\t=cmd"),
    ],
)
def test_spreadsheet_safe_neutralizes_formulas(value, expected):
    assert _spreadsheet_safe(value) == expected


def test_metric_text_and_filename_helpers():
    assert _metric_text(None) == "N/A"
    assert _metric_text(0.91234) == "91.23%"
    assert _filename("run_abc-1", "csv") == "evaluation-run_abc-1.csv"
    assert _filename('run"; rm -rf /', "pdf") == "evaluation-run___rm_-rf__.pdf"


def test_timestamp_marks_naive_values_as_utc():
    assert _timestamp(SimpleNamespace(timestamp=datetime(2026, 1, 2, 3, 4, 5))) == "2026-01-02T03:04:05Z"
    aware = datetime(2026, 1, 2, tzinfo=timezone.utc)
    assert _timestamp(SimpleNamespace(timestamp=aware)) == "2026-01-02T00:00:00+00:00"
