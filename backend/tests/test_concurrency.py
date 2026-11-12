"""Concurrency gate tests, including parallel request isolation."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import get_db
from app.main import app
from app.ml.gate import EvaluationGate, GateTimeout
from app.models import Base, User
from app.security import create_token
from app.services import evaluation_service
from tests.ml_helpers import eval_body, put_dataset, synthetic_df

N = 20


def test_gate_bounds_parallel_work_and_releases_slots():
    gate = EvaluationGate(max_concurrent=2, queue_timeout=10)
    finished = []
    def job(index):
        with gate.slot():
            time.sleep(0.02)
            finished.append(index)
    with ThreadPoolExecutor(10) as pool:
        list(pool.map(job, range(10)))
    assert sorted(finished) == list(range(10))
    assert gate.stats()["peak_running"] <= 2
    assert gate.stats()["running"] == 0 and gate.stats()["waiting"] == 0


def test_gate_timeout_is_recoverable():
    gate = EvaluationGate(max_concurrent=1, queue_timeout=.05)
    with gate.slot():
        try:
            with gate.slot():
                raise AssertionError("second slot should time out")
        except GateTimeout:
            pass
    with gate.slot():
        assert gate.stats()["running"] == 1


def test_twenty_simultaneous_evaluations_do_not_mix_user_data(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'parallel.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override
    monkeypatch.setenv("DATASET_DIR", str(tmp_path / "datasets"))
    try:
        with Session() as db:
            users = [User(username=f"user{i}", email=f"user{i}@example.com", password_hash="x") for i in range(N)]
            db.add_all(users)
            db.commit()
            user_data = [(user.user_id, {"Authorization": f"Bearer {create_token(user.user_id)}"}) for user in users]
        jobs = []
        for index, (user_id, headers) in enumerate(user_data):
            frame = synthetic_df(100 + index * 3, 6, seed=index)
            dataset_id = put_dataset(frame, f"user{index}.csv", owner_id=user_id)
            jobs.append((index, user_id, headers, frame, dataset_id))
        barrier = threading.Barrier(N)
        def call(job):
            index, user_id, headers, frame, dataset_id = job
            client = TestClient(app)
            barrier.wait()
            return client.post("/evaluations", headers=headers, json=eval_body(
                dataset_id, frame, "label", ["logistic_regression", "decision_tree"]))
        with ThreadPoolExecutor(N) as pool:
            responses = list(pool.map(call, jobs))
        assert [response.status_code for response in responses] == [200] * N
        for (index, user_id, headers, frame, _), response in zip(jobs, responses):
            payload = response.json()
            assert payload["dataset"]["name"] == f"user{index}.csv"
            assert payload["dataset"]["rows"] == len(frame)
            history = TestClient(app).get("/history", headers=headers).json()
            assert history["total"] == 1 and history["items"][0]["run_id"] == payload["run_id"]
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_busy_server_returns_503_and_retry_after(client, dataset_dir, monkeypatch):
    gate = EvaluationGate(max_concurrent=1, queue_timeout=.05)
    monkeypatch.setattr(evaluation_service, "evaluation_gate", gate)
    frame = synthetic_df(100, 4)
    body = eval_body(put_dataset(frame), frame, "label", ["decision_tree"])
    with gate.slot():
        response = client.post("/evaluations", json=body)
    assert response.status_code == 503 and response.headers["retry-after"] == "5"
    assert client.post("/evaluations", json=body).status_code == 200
