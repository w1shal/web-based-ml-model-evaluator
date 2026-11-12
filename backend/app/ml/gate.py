"""Bound in-process model-evaluation concurrency and request queueing."""
import logging
import os
import threading
from contextlib import contextmanager

log = logging.getLogger(__name__)


class GateTimeout(Exception):
    """Raised when an evaluation cannot acquire a worker slot before timeout."""


class EvaluationGate:
    def __init__(self, max_concurrent: int, queue_timeout: float):
        if int(max_concurrent) < 1:
            raise ValueError("max_concurrent must be at least 1")
        if float(queue_timeout) < 0:
            raise ValueError("queue_timeout cannot be negative")
        self.max_concurrent = int(max_concurrent)
        self.queue_timeout = float(queue_timeout)
        self._semaphore = threading.BoundedSemaphore(self.max_concurrent)
        self._lock = threading.Lock()
        self._running = 0
        self._waiting = 0
        self.peak_running = 0

    @contextmanager
    def slot(self):
        with self._lock:
            self._waiting += 1
        acquired = self._semaphore.acquire(timeout=self.queue_timeout)
        with self._lock:
            self._waiting -= 1
            if acquired:
                self._running += 1
                self.peak_running = max(self.peak_running, self._running)
        if not acquired:
            raise GateTimeout()
        try:
            yield
        finally:
            with self._lock:
                self._running -= 1
            self._semaphore.release()

    def stats(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "waiting": self._waiting,
                "max_concurrent": self.max_concurrent,
                "peak_running": self.peak_running,
            }


def _from_env() -> EvaluationGate:
    default_slots = max(2, min(4, os.cpu_count() or 1))
    return EvaluationGate(
        int(os.getenv("EVAL_MAX_CONCURRENT", default_slots)),
        float(os.getenv("EVAL_QUEUE_TIMEOUT", "300")),
    )


evaluation_gate = _from_env()
