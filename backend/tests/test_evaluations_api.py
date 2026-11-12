from tests.ml_helpers import cancer_df, dataset_dir, eval_body, iris_df, put_dataset  # noqa: F401


def test_guest_can_run_an_evaluation(client, dataset_dir):
    frame = iris_df()
    dataset_id = put_dataset(frame, "iris.csv")
    response = client.post("/evaluations", json=eval_body(dataset_id, frame, "species", ["decision_tree", "knn"]))
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"].startswith("run_") and body["status"] == "completed"
    assert body["dataset"]["name"] == "iris.csv" and body["dataset"]["rows"] == 150
    assert [result["algorithm"] for result in body["results"]] == ["decision_tree", "knn"]
    assert {"accuracy", "precision", "recall", "f1_score"} <= body["results"][0].keys()


def test_logged_in_user_can_run_an_evaluation(client, make_user, dataset_dir):
    user = make_user("alice")
    frame = cancer_df()
    dataset_id = put_dataset(frame, "cancer.csv", owner_id=user["user_id"])
    response = client.post("/evaluations", json=eval_body(dataset_id, frame, "diagnosis", ["svm"]), headers=user["headers"])
    assert response.status_code == 200 and response.json()["results"][0]["algorithm"] == "svm"


def test_users_cannot_run_evaluations_on_another_users_dataset(client, make_user, dataset_dir):
    owner, other = make_user("alice"), make_user("bob")
    frame = iris_df()
    dataset_id = put_dataset(frame, owner_id=owner["user_id"])
    body = eval_body(dataset_id, frame, "species", ["knn"])
    assert client.post("/evaluations", json=body, headers=other["headers"]).status_code == 404
    assert client.post("/evaluations", json=body).status_code == 404
    assert client.post("/evaluations", json=body, headers=owner["headers"]).status_code == 200


def test_unknown_dataset_and_path_traversal_return_404(client, dataset_dir):
    frame = iris_df()
    for invalid_id in ("ds_doesnotexist", "../../etc/passwd", "..\\secret"):
        response = client.post("/evaluations", json=eval_body(invalid_id, frame, "species", ["knn"]))
        assert response.status_code == 404


def test_bad_requests_return_400(client, dataset_dir):
    frame = iris_df()
    dataset_id = put_dataset(frame)
    valid = eval_body(dataset_id, frame, "species", ["knn"])
    assert client.post("/evaluations", json={}).status_code == 400
    assert client.post("/evaluations", content=b"{not json", headers={"Content-Type": "application/json"}).status_code == 400
    assert client.post("/evaluations", json={**valid, "algorithms": []}).status_code == 400
    assert client.post("/evaluations", json={**valid, "algorithms": ["magic"]}).status_code == 400
    assert client.post("/evaluations", json={**valid, "algorithms": ["knn"] * 6}).status_code == 400
    assert client.post("/evaluations", json={**valid, "test_size": 0}).status_code == 400
    assert client.post("/evaluations", json={**valid, "test_size": 0.9}).status_code == 400
    assert client.post("/evaluations", json={**valid, "missing_value_strategy": "guess"}).status_code == 400
    assert client.post("/evaluations", json={**valid, "feature_columns": ["species", "petal_width"]}).status_code == 400
    assert client.post("/evaluations", json={**valid, "feature_columns": ["unknown"]}).status_code == 400


def test_unprocessable_data_returns_422(client, dataset_dir):
    frame = iris_df().assign(species=1)
    dataset_id = put_dataset(frame)
    response = client.post("/evaluations", json=eval_body(dataset_id, frame, "species", ["knn"]))
    assert response.status_code == 422 and "two different classes" in response.json()["detail"]


def test_invalid_token_is_rejected(client, dataset_dir):
    frame = iris_df()
    dataset_id = put_dataset(frame)
    response = client.post("/evaluations", json=eval_body(dataset_id, frame, "species", ["knn"]),
                           headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401


def test_corrupt_stored_dataset_is_422(client, dataset_dir):
    (dataset_dir / "ds_corrupt.csv").write_bytes(b"")
    response = client.post("/evaluations", json={
        "dataset_id": "ds_corrupt", "target_column": "y",
        "feature_columns": ["a"], "algorithms": ["knn"]
    })
    assert response.status_code == 422
