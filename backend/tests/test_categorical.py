import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

from app.ml.algorithms import BUILTIN_IDS
from app.ml.errors import EvaluationError
from app.ml.evaluator import EvaluationConfig, run_evaluation
from tests.ml_helpers import features_of, iris_df, put_dataset


def categorical_df(n=240, seed=3):
    rng = np.random.default_rng(seed)
    colour = rng.choice(["red", "green", "blue"], n)
    size = rng.choice(["S", "M", "L", "XL"], n)
    x = rng.normal(size=n)
    target = np.where((colour == "red") | ((size == "XL") & (x > 0)), "yes", "no")
    return pd.DataFrame({"x": x, "colour": colour, "size": size, "buy": target})


def config(frame, algorithms, **kwargs):
    return EvaluationConfig("buy", features_of(frame, "buy"), list(algorithms), **kwargs)


def test_one_hot_encoding_handles_string_features_and_target():
    frame = categorical_df()
    result = run_evaluation(frame, config(frame, ["decision_tree"]))
    row = result["results"][0]
    assert result["preprocessing"]["categorical_features"] == ["colour", "size"]
    assert result["preprocessing"]["categorical_encoding"] == "one_hot"
    assert row["classes"] == ["no", "yes"]
    encoded = pd.concat([frame[["x"]], pd.get_dummies(frame[["colour", "size"]], dtype=float)], axis=1)
    x_train, x_test, y_train, y_test = train_test_split(encoded, frame["buy"], test_size=0.2, random_state=42, stratify=frame["buy"])
    reference = DecisionTreeClassifier(random_state=42).fit(x_train, y_train).predict(x_test)
    assert row["accuracy"] == pytest.approx(accuracy_score(y_test, reference), abs=1e-6)


def test_all_builtin_models_handle_categorical_columns():
    result = run_evaluation(categorical_df(), config(categorical_df(), BUILTIN_IDS))
    assert result["status"] == "completed"
    assert all(row["status"] == "completed" for row in result["results"])


def test_unseen_categories_are_ignored():
    frame = categorical_df()
    frame.loc[0, "colour"] = "ultraviolet"
    assert run_evaluation(frame, config(frame, BUILTIN_IDS))["status"] == "completed"


def test_missing_categorical_values_are_imputed_or_dropped():
    frame = categorical_df()
    frame.loc[:19, "colour"] = np.nan
    imputed = run_evaluation(frame, config(frame, ["knn"]))
    assert imputed["preprocessing"]["missing_cells_by_column"] == {"colour": 20}
    assert imputed["preprocessing"]["imputation_categorical"] == "most_frequent"
    dropped = run_evaluation(frame, config(frame, ["knn"], missing_value_strategy="drop_rows"))
    assert dropped["preprocessing"]["rows_dropped_missing_features"] == 20


def test_mixed_type_categories_and_boolean_features():
    frame = categorical_df()
    frame["mixed"] = pd.Series([7 if i % 2 == 0 else "seven" for i in range(len(frame))], dtype=object)
    frame["flag"] = frame["x"] > 0
    outcome = run_evaluation(frame, config(frame, ["decision_tree"]))
    assert outcome["status"] == "completed"
    assert "mixed" in outcome["preprocessing"]["categorical_features"]
    assert "flag" in outcome["preprocessing"]["numeric_features"]


def test_too_many_categories_are_rejected_with_422():
    frame = categorical_df()
    frame["id_like"] = [f"id{i}" for i in range(len(frame))]
    with pytest.raises(EvaluationError) as exc:
        run_evaluation(frame, config(frame, ["knn"]))
    assert exc.value.status_code == 422 and exc.value.code == "TOO_MANY_CATEGORIES"


def test_categorical_dataset_works_through_api(client, dataset_dir):
    frame = categorical_df()
    dataset_id = put_dataset(frame)
    response = client.post("/evaluations", json={
        "dataset_id": dataset_id, "target_column": "buy",
        "feature_columns": features_of(frame, "buy"), "algorithms": ["decision_tree", "random_forest"]
    })
    assert response.status_code == 200 and response.json()["results"][0]["classes"] == ["no", "yes"]
