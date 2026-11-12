from sklearn.dummy import DummyClassifier

from app.ml.comparison import compare
from app.ml.registry import AlgorithmSpec, register_algorithm, unregister_algorithm
from tests.ml_helpers import cancer_df, iris_df, put_dataset, eval_body


def run_evaluation_api(client, frame, target, algorithms, headers=None, owner_id=None, name="data.csv"):
    dataset_id = put_dataset(frame, name, owner_id=owner_id)
    response = client.post("/evaluations", json=eval_body(dataset_id, frame, target, algorithms), headers=headers or {})
    assert response.status_code == 200, response.text
    return response.json()


def test_authenticated_run_is_saved_to_history_and_guest_run_is_not(client, make_user, dataset_dir, session_factory):
    user = make_user("alice")
    frame = iris_df()
    created = run_evaluation_api(client, frame, "species", ["decision_tree", "knn"],
                                 user["headers"], user["user_id"], "iris.csv")
    run_evaluation_api(client, frame, "species", ["knn"], name="guest.csv")
    history = client.get("/history", headers=user["headers"]).json()
    assert [item["run_id"] for item in history["items"]] == [created["run_id"]]
    assert history["items"][0]["dataset_name"] == "iris.csv"
    detail = client.get(f"/history/{created['run_id']}", headers=user["headers"]).json()
    assert set(detail["confusion_matrices"]) == {"decision_tree", "knn"}
    from app.models import EvaluationRun
    with session_factory() as db:
        stored = db.get(EvaluationRun, created["run_id"])
        assert stored.results[0].serialized_metrics["class_labels"] == [0, 1, 2]


def test_get_evaluation_round_trips_exact_response(client, make_user, dataset_dir):
    user = make_user("alice")
    created = run_evaluation_api(client, cancer_df(), "diagnosis",
                                 ["logistic_regression", "svm", "random_forest"], user["headers"], user["user_id"])
    fetched = client.get(f"/evaluations/{created['run_id']}", headers=user["headers"])
    assert fetched.status_code == 200 and fetched.json() == created


def test_guest_run_can_be_retrieved_by_generated_run_id(client, dataset_dir):
    created = run_evaluation_api(client, iris_df(), "species", ["knn"])
    fetched = client.get(f"/evaluations/{created['run_id']}")
    assert fetched.status_code == 200 and fetched.json() == created


def test_run_access_is_limited_to_owner(client, make_user, dataset_dir):
    owner, other = make_user("alice"), make_user("bob")
    created = run_evaluation_api(client, iris_df(), "species", ["knn"], owner["headers"], owner["user_id"])
    url = f"/evaluations/{created['run_id']}"
    assert client.get(url, headers=owner["headers"]).status_code == 200
    assert client.get(url, headers=other["headers"]).status_code == 403
    assert client.get(url).status_code == 401
    assert client.get("/evaluations/run_unknown", headers=owner["headers"]).status_code == 404


def test_partial_run_is_saved_and_retrievable(client, make_user, dataset_dir):
    class Boom(DummyClassifier):
        def fit(self, X, y, *args, **kwargs):
            raise RuntimeError("internal detail")
    register_algorithm(AlgorithmSpec(id="boom_algo", name="Boom", factory=lambda seed, rows: Boom()))
    try:
        user = make_user("alice")
        created = run_evaluation_api(client, iris_df(), "species", ["boom_algo", "decision_tree"], user["headers"], user["user_id"])
    finally:
        unregister_algorithm("boom_algo")
    assert created["status"] == "partial"
    failed, passed = created["results"]
    assert failed["status"] == "failed" and "internal detail" not in failed["error"] and "accuracy" not in failed
    assert passed["status"] == "completed"
    assert client.get(f"/evaluations/{created['run_id']}", headers=user["headers"]).json() == created


def test_comparison_ranks_results_deterministically(client, dataset_dir):
    created = run_evaluation_api(client, cancer_df(), "diagnosis",
                                 ["decision_tree", "logistic_regression", "knn", "svm"])
    ranking = created["comparison"]["ranking"]
    values = [item["f1_score"] for item in ranking]
    assert values == sorted(values, reverse=True)
    assert [item["rank"] for item in ranking] == [1, 2, 3, 4]
    assert created["comparison"]["best_by_metric"]["f1_score"] == ranking[0]["algorithm"]


def test_comparison_ties_use_accuracy_then_algorithm_id():
    tied = [
        {"algorithm": "b_algo", "status": "completed", "f1_score": .9, "accuracy": .9},
        {"algorithm": "a_algo", "status": "completed", "f1_score": .9, "accuracy": .9},
        {"algorithm": "c_algo", "status": "completed", "f1_score": .9, "accuracy": .95},
        {"algorithm": "x_fail", "status": "failed"},
    ]
    assert [row["algorithm"] for row in compare(tied)["ranking"]] == ["c_algo", "a_algo", "b_algo"]
    assert compare(list(reversed(tied)))["ranking"] == compare(tied)["ranking"]
