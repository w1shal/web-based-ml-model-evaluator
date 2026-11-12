import pandas as pd
import pytest
from app.ml.errors import EvaluationError
from app.ml.evaluator import EvaluationConfig, run_evaluation
from app.ml.preprocessing import prepare_data


def sample_frame():
    rows = []
    for i in range(120):
        rows.append({
            "age": 18 + (i % 50),
            "income": float(25000 + (i * 317) % 80000),
            "region": ["north", "south", "west"][i % 3],
            "plan": ["basic", "plus"][i % 2],
            "outcome": "yes" if i % 3 == 0 else "no",
        })
    return pd.DataFrame(rows)


def test_prepare_data_detects_numeric_and_categorical_columns_and_encodes_target():
    prepared = prepare_data(sample_frame(), "outcome", ["age", "region", "plan"], "median_imputation")
    assert prepared.numeric_cols == ["age"]
    assert prepared.categorical_cols == ["region", "plan"]
    assert prepared.classes == ["no", "yes"]
    assert len(prepared.y) == 120


def test_evaluation_trains_with_mixed_numeric_and_categorical_features():
    frame = sample_frame()
    result = run_evaluation(frame, EvaluationConfig(
        target_column="outcome",
        feature_columns=["age", "income", "region", "plan"],
        algorithms=["decision_tree", "logistic_regression"],
    ))
    assert result["status"] == "completed"
    assert all(row["status"] == "completed" for row in result["results"])
    assert result["preprocessing"]["categorical_features"] == ["region", "plan"]


def test_most_frequent_imputation_handles_missing_categories():
    frame = sample_frame()
    frame.loc[[2, 5, 8], "region"] = None
    result = run_evaluation(frame, EvaluationConfig(
        target_column="outcome", feature_columns=["age", "region"],
        algorithms=["decision_tree"], missing_value_strategy="median_imputation",
    ))
    assert result["status"] == "completed"


def test_drop_rows_strategy_drops_missing_categorical_rows():
    frame = sample_frame()
    frame.loc[[2, 5, 8], "region"] = None
    prepared = prepare_data(frame, "outcome", ["age", "region"], "drop_rows")
    assert prepared.info["rows_dropped_missing_features"] == 3
    assert prepared.info["rows_used"] == 117


def test_unseen_category_at_transform_time_is_ignored_by_one_hot_encoder():
    from app.ml.preprocessing import build_preprocessor
    frame = sample_frame()
    prepared = prepare_data(frame, "outcome", ["age", "region"], "median_imputation")
    preprocessor = build_preprocessor(prepared.numeric_cols, prepared.categorical_cols, False)
    preprocessor.fit(prepared.X.iloc[:90])
    transformed = preprocessor.transform(pd.DataFrame({"age": [30], "region": ["east"]}))
    assert transformed.shape[0] == 1


def test_high_cardinality_categorical_feature_is_rejected():
    frame = sample_frame()
    frame["session"] = [f"session-{i}" for i in range(len(frame))]
    with pytest.raises(EvaluationError) as error:
        prepare_data(frame, "outcome", ["session"], "median_imputation")
    assert error.value.code == "TOO_MANY_CATEGORIES"
