from datetime import datetime, timezone

from app.models import EvaluationRun, User
from app.services.history import list_runs, persist_completed_evaluation


RESULTS = [
    {
        "algorithm": "random_forest",
        "accuracy": 0.94,
        "precision": 0.93,
        "recall": 0.92,
        "f1_score": 0.925,
        "roc_auc": 0.97,
        "confusion_matrix": [[40, 2], [3, 55]],
        "class_labels": ["negative", "positive"],
    }
]


def _create_user(session_factory, username="history-owner"):
    with session_factory() as db:
        user = User(
            username=username,
            email=f"{username}@example.com",
            password_hash="test-only-hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.user_id


def test_completed_evaluation_persists_authenticated_user_and_all_metadata(
    session_factory,
):
    user_id = _create_user(session_factory)
    completed_at = datetime(2026, 11, 12, 8, 30, tzinfo=timezone.utc)

    with session_factory() as db:
        user = db.get(User, user_id)
        run = persist_completed_evaluation(
            db,
            user,
            dataset_name="customer_churn.csv",
            target_column="churn",
            feature_columns=["age", "tenure", "monthly_charges"],
            split_ratio=0.25,
            results=RESULTS,
            timestamp=completed_at,
        )
        run_id = run.run_id

    # Verify from a fresh DB session: this is persisted, not just in-memory.
    with session_factory() as db:
        saved = db.get(EvaluationRun, run_id)
        assert saved is not None
        assert saved.user_id == user_id
        assert saved.dataset_name == "customer_churn.csv"
        assert saved.target_column == "churn"
        assert saved.feature_columns == ["age", "tenure", "monthly_charges"]
        assert saved.split_ratio == 0.25
        assert saved.status == "completed"
        assert saved.timestamp == completed_at.replace(tzinfo=None)
        assert len(saved.results) == 1
        metric = saved.results[0]
        assert metric.algorithm_name == "random_forest"
        assert metric.accuracy == 0.94
        assert metric.confusion_matrix == [[40, 2], [3, 55]]
        assert metric.serialized_metrics["class_labels"] == [
            "negative",
            "positive",
        ]


def test_guest_completed_evaluation_is_not_in_any_users_history(
    session_factory,
):
    user_id = _create_user(session_factory, "registered-user")

    with session_factory() as db:
        guest_run = persist_completed_evaluation(
            db,
            None,
            dataset_name="guest_dataset.csv",
            target_column="label",
            feature_columns=["feature_a"],
            split_ratio=0.2,
            results=RESULTS,
        )
        guest_run_id = guest_run.run_id

    with session_factory() as db:
        stored_guest_run = db.get(EvaluationRun, guest_run_id)
        assert stored_guest_run is not None
        assert stored_guest_run.user_id is None

        items, total = list_runs(db, user_id)
        assert items == []
        assert total == 0


def test_each_user_only_receives_runs_created_for_their_verified_identity(
    session_factory,
):
    alice_id = _create_user(session_factory, "alice")
    bob_id = _create_user(session_factory, "bob")

    with session_factory() as db:
        alice = db.get(User, alice_id)
        bob = db.get(User, bob_id)
        alice_run = persist_completed_evaluation(
            db,
            alice,
            dataset_name="alice.csv",
            target_column="label",
            feature_columns=["a"],
            split_ratio=0.2,
            results=RESULTS,
        )
        bob_run = persist_completed_evaluation(
            db,
            bob,
            dataset_name="bob.csv",
            target_column="label",
            feature_columns=["b"],
            split_ratio=0.3,
            results=RESULTS,
        )
        alice_run_id = alice_run.run_id
        bob_run_id = bob_run.run_id

    with session_factory() as db:
        alice_items, alice_total = list_runs(db, alice_id)
        bob_items, bob_total = list_runs(db, bob_id)

        assert alice_total == 1
        assert bob_total == 1
        assert [item.run_id for item in alice_items] == [alice_run_id]
        assert [item.run_id for item in bob_items] == [bob_run_id]
        assert bob_run_id not in {item.run_id for item in alice_items}
        assert alice_run_id not in {item.run_id for item in bob_items}


def test_history_query_returns_empty_collection_for_new_user(session_factory):
    user_id = _create_user(session_factory, "empty-user")

    with session_factory() as db:
        items, total = list_runs(db, user_id, limit=50, offset=0)

    assert items == []
    assert total == 0
