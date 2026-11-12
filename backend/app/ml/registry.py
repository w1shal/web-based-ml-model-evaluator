"""Algorithm registry and adapter contract (ENG-01)."""
import re
from dataclasses import dataclass
from typing import Any, Callable

from .errors import EvaluationError

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,39}$")

@dataclass(frozen=True)
class AlgorithmSpec:
    id: str
    name: str
    factory: Callable[[int, int], Any]
    needs_scaling: bool = False
    description: str = ""

_REGISTRY: dict[str, AlgorithmSpec] = {}

def register_algorithm(spec: AlgorithmSpec, *, replace: bool = False) -> None:
    if not _ID_RE.fullmatch(spec.id):
        raise ValueError(f"Invalid algorithm id: {spec.id!r}")
    if spec.id in _REGISTRY and not replace:
        raise ValueError(f"Algorithm already registered: {spec.id}")
    _REGISTRY[spec.id] = spec

def unregister_algorithm(algorithm_id: str) -> None:
    _REGISTRY.pop(algorithm_id, None)

def get_algorithm(algorithm_id: str) -> AlgorithmSpec:
    try:
        return _REGISTRY[algorithm_id]
    except KeyError:
        raise EvaluationError("UNKNOWN_ALGORITHM", f"Unknown algorithm: {algorithm_id}", 400) from None

def list_algorithms() -> list[AlgorithmSpec]:
    return list(_REGISTRY.values())
