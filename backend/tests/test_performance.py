"""MLE-NF-001: benchmark the evaluation engine on a 10,000 x 50 dataset."""
import time

import numpy as np
import pandas as pd
import pytest

from app.ml.algorithms import BUILTIN_IDS
from app.ml.evaluator import EvaluationConfig, run_evaluation

LIMIT_SECONDS = 15
pytestmark = pytest.mark.performance


@pytest.fixture(scope="module")
def large_binary_dataset():
    rng = np.random.RandomState(42)
    values = rng.normal(size=(10_000, 50))
    frame = pd.DataFrame(values, columns=[f"feature_{index}" for index in range(50)])
    frame["label"] = (values[:, :5].sum(axis=1) > 0).astype(int)
    return frame


def evaluate(frame, algorithms):
    features = [column for column in frame.columns if column != "label"]
    return run_evaluation(frame, EvaluationConfig("label", features, algorithms))


@pytest.mark.parametrize("algorithm", BUILTIN_IDS)
def test_single_algorithm_performance_target(algorithm, large_binary_dataset):
    started = time.perf_counter()
    result = evaluate(large_binary_dataset, [algorithm])
    elapsed = time.perf_counter() - started
    assert result["status"] == "completed"
    assert elapsed < LIMIT_SECONDS, f"{algorithm} took {elapsed:.2f}s (limit {LIMIT_SECONDS}s)"


def test_all_five_algorithms_performance_target(large_binary_dataset):
    started = time.perf_counter()
    result = evaluate(large_binary_dataset, list(BUILTIN_IDS))
    elapsed = time.perf_counter() - started
    assert result["status"] == "completed"
    assert elapsed < LIMIT_SECONDS, f"all five algorithms took {elapsed:.2f}s (limit {LIMIT_SECONDS}s)"
