"""Evaluation use case: load an owned dataset, run models and shape the response."""
from typing import Optional

from ..ml.evaluator import EvaluationConfig, run_evaluation
from ..schemas_evaluation import EvaluationRequest
from . import dataset_store
from .history import new_run_id


def execute_evaluation(user_id: Optional[int], request: EvaluationRequest) -> dict:
    dataset = dataset_store.load_dataset(request.dataset_id, user_id)
    outcome = run_evaluation(dataset.df, EvaluationConfig(
        target_column=request.target_column,
        feature_columns=request.feature_columns,
        algorithms=request.algorithms,
        test_size=request.test_size,
        missing_value_strategy=request.missing_value_strategy,
    ))
    return {
        "run_id": new_run_id(),
        "status": outcome["status"],
        "dataset": {"name": dataset.name, **outcome["dataset"]},
        "results": outcome["results"],
        "preprocessing": outcome["preprocessing"],
    }
