"""In-memory sliding-window rate limiting for authentication endpoints.

Counters are per process. Deployments with multiple API workers or replicas
should replace the storage backend with a shared store such as Redis.
"""

import math
import os
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request


class SlidingWindowLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self.clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Record an attempt and return (allowed, retry_after_seconds)."""
        if limit < 1 or window < 1:
            raise ValueError("Rate-limit count and window must be positive integers")

        now = self.clock()
        with self._lock:
            attempts = self._hits[key]

            while attempts and now - attempts[0] >= window:
                attempts.popleft()

            if len(attempts) >= limit:
                retry_after = max(1, math.ceil(window - (now - attempts[0])))
                return False, retry_after

            attempts.append(now)
            return True, 0

    def reset(self) -> None:
        """Clear counters and restore the monotonic clock (used by tests)."""
        with self._lock:
            self._hits.clear()
            self.clock = time.monotonic


limiter = SlidingWindowLimiter()


def _positive_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        value = int(raw) if raw is not None else default
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a positive integer") from exc

    if value < 1:
        raise RuntimeError(f"{name} must be a positive integer")
    return value


def client_ip(request: Request) -> str:
    """Use X-Forwarded-For only when TRUST_PROXY is explicitly enabled."""
    trust_proxy = os.getenv("TRUST_PROXY", "").strip().lower() in {
        "1", "true", "yes", "on"
    }
    if trust_proxy:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            candidate = forwarded_for.split(",", 1)[0].strip()
            if candidate:
                return candidate

    return request.client.host if request.client else "unknown"


def rate_limit(scope: str, default_limit: int, default_window: int = 60):
    """Build a FastAPI dependency for configurable per-IP request limits."""

    def dependency(request: Request) -> None:
        limit = _positive_int_env(
            f"RATE_LIMIT_{scope.upper()}_MAX",
            default_limit,
        )
        window = _positive_int_env("RATE_LIMIT_WINDOW", default_window)

        allowed, retry_after = limiter.hit(
            f"{scope}:{client_ip(request)}",
            limit,
            window,
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
