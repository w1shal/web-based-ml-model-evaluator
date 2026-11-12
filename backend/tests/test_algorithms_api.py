def test_algorithms_endpoint_lists_all_registered_algorithms(client):
    response = client.get("/algorithms")
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == [
        "logistic_regression", "decision_tree", "random_forest", "svm", "knn"
    ]
