"""Validation and resolution of user-selected algorithm IDs (MLE-F-014)."""
from .errors import EvaluationError
from .registry import AlgorithmSpec, get_algorithm

MAX_ALGORITHMS_PER_RUN = 5

def resolve_selection(algorithm_ids: list[str]) -> list[AlgorithmSpec]:
    if not algorithm_ids:
        raise EvaluationError("NO_ALGORITHM", "Select at least one algorithm", 400)
    unique_ids = list(dict.fromkeys(algorithm_ids))
    if len(unique_ids) > MAX_ALGORITHMS_PER_RUN:
        raise EvaluationError("TOO_MANY_ALGORITHMS", "Select no more than 5 algorithms per run", 400)
    return [get_algorithm(algorithm_id) for algorithm_id in unique_ids]
