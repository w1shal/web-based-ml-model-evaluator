"""MLE-NF-001: benchmark a 10,000 x 50 classification dataset on a demo machine."""
import time

import pytest

from app.ml.algorithms import BUILTIN_IDS
from app.ml.evaluator import EvaluationConfig, run_evaluation
from tests.ml_helpers import features_of, synthetic_df

LIMIT_SECONDS = 15
pytestmark = pytest.mark.performance


@pytest.fixture(scope="module")
def large_binary_dataset():
    return synthetic_df(10_000, 50, classes=2)


@pytest.mark.parametrize("algorithm", BUILTIN_IDS)
def test_each_builtin_algorithm_meets_single_algorithm_target(algorithm, large_binary_dataset):
    started = time.perf_counter()
    result = run_evaluation(large_binary_dataset, EvaluationConfig(
        "label", features_of(large_binary_dataset, "label"), [algorithm]))
    assert result["status"] == "completed"
    assert time.perf_counter() - started < LIMIT_SECONDS


def test_all_five_algorithms_together_meet_target(large_binary_dataset):
    started = time.perf_counter()
    result = run_evaluation(large_binary_dataset, EvaluationConfig(
        "label", features_of(large_binary_dataset, "label"), list(BUILTIN_IDS)))
    assert result["status"] == "completed"
    assert time.perf_counter() - started < LIMIT_SECONDS
