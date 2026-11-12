"""Concurrency and result-persistence tests for evaluation requests."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from app.ml.gate import EvaluationGate, GateTimeout
from app.services import dataset_store, evaluation_service


def sample_frame(rows=120):
    return pd.DataFrame({
        "feature_a": [i % 17 for i in range(rows)],
        "feature_b": [float((i * 7) % 31) for i in range(rows)],
        "target": ["yes" if i % 2 else "no" for i in range(rows)],
    })


def make_dataset(frame, tmp_path, owner_id=None):
    return dataset_store.store_dataset(frame.to_csv(index=False).encode("utf-8"), "sample.csv", owner_id)


def request_body(dataset_id):
    return {
        "dataset_id": dataset_id,
        "target_column": "target",
        "feature_columns": ["feature_a", "feature_b"],
        "algorithms": ["decision_tree"],
        "test_size": 0.2,
        "missing_value_strategy": "median_imputation",
    }


def test_gate_bounds_parallel_work_and_releases_slots():
    gate = EvaluationGate(max_concurrent=2, queue_timeout=5)
    completed = []
    def job(index):
        with gate.slot():
            time.sleep(0.01)
            completed.append(index)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(job, range(16)))
    assert sorted(completed) == list(range(16))
    assert gate.stats()["peak_running"] <= 2
    assert gate.stats()["running"] == 0
    assert gate.stats()["waiting"] == 0


def test_gate_timeout_is_recoverable():
    gate = EvaluationGate(max_concurrent=1, queue_timeout=0.02)
    with gate.slot():
        try:
            with gate.slot():
                raise AssertionError("expected queue timeout")
        except GateTimeout:
            pass
    with gate.slot():
        assert gate.stats()["running"] == 1


def test_evaluation_is_persisted_and_round_trips(client, make_user, tmp_path, monkeypatch):
    monkeypatch.setenv("DATASET_DIR", str(tmp_path / "datasets"))
    user = make_user("evaluator")
    frame = sample_frame()
    dataset_id = make_dataset(frame, tmp_path, owner_id=user["user_id"])
    response = client.post("/evaluations", json=request_body(dataset_id), headers=user["headers"])
    assert response.status_code == 200, response.text
    created = response.json()
    fetched = client.get(f"/evaluations/{created['run_id']}", headers=user["headers"])
    assert fetched.status_code == 200
    assert fetched.json() == created
    history = client.get("/history", headers=user["headers"])
    assert history.status_code == 200
    assert history.json()["total"] == 1


def test_guest_run_can_be_retrieved_but_owned_run_is_private(client, make_user, tmp_path, monkeypatch):
    monkeypatch.setenv("DATASET_DIR", str(tmp_path / "datasets"))
    frame = sample_frame()
    guest_dataset_id = make_dataset(frame, tmp_path)
    guest = client.post("/evaluations", json=request_body(guest_dataset_id))
    assert guest.status_code == 200, guest.text
    run_id = guest.json()["run_id"]
    assert client.get(f"/evaluations/{run_id}").status_code == 200

    user = make_user("owner")
    owned_dataset_id = make_dataset(frame, tmp_path, owner_id=user["user_id"])
    owned = client.post("/evaluations", json=request_body(owned_dataset_id), headers=user["headers"])
    assert owned.status_code == 200, owned.text
    owned_id = owned.json()["run_id"]
    assert client.get(f"/evaluations/{owned_id}").status_code == 401


def test_busy_server_returns_503_and_retry_after(client, tmp_path, monkeypatch):
    monkeypatch.setenv("DATASET_DIR", str(tmp_path / "datasets"))
    gate = EvaluationGate(max_concurrent=1, queue_timeout=0.01)
    monkeypatch.setattr(evaluation_service, "evaluation_gate", gate)
    frame = sample_frame()
    dataset_id = make_dataset(frame, tmp_path)
    with gate.slot():
        response = client.post("/evaluations", json=request_body(dataset_id))
    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"
    response = client.post("/evaluations", json=request_body(dataset_id))
    assert response.status_code == 200
