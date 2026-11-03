"""MLE-SEC-005: sliding-window rate limiting for authentication endpoints.

In-memory and per-process: fine for a single container. With several workers or
servers, move the counters to Redis (the interface below would stay the same).
"""
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from .config import trust_proxy


class SlidingWindowLimiter:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Record an attempt. Returns (allowed, retry_after_seconds)."""
        now = self.clock()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] >= window:
                q.popleft()
            if len(q) >= limit:
                return False, max(1, int(window - (now - q[0])) + 1)
            q.append(now)
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
        self.clock = time.monotonic


limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    if trust_proxy():
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(scope: str, default_limit: int, default_window: int = 60):
    """FastAPI dependency factory. Limits are read per request so they can be set via env."""
    def dependency(request: Request):
        limit = int(os.getenv(f"RATE_LIMIT_{scope.upper()}_MAX", default_limit))
        window = int(os.getenv("RATE_LIMIT_WINDOW", default_window))
        allowed, retry_after = limiter.hit(f"{scope}:{client_ip(request)}", limit, window)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )
    return dependency
