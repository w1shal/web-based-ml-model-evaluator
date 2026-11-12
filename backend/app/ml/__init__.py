"""Evaluation engine. Pure Python/scikit-learn: no FastAPI or database imports in this package."""
from . import algorithms  # noqa: F401  (registers the built-in algorithms)
from .errors import EvaluationError  # noqa: F401
