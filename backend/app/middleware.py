"""MLE-SEC-004: HTTPS enforcement (defence in depth behind the TLS-terminating proxy) and basic headers."""
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import enforce_https


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        https_mode = enforce_https()
        if https_mode:
            proto = request.headers.get("x-forwarded-proto", request.url.scheme).split(",")[0].strip().lower()
            if proto != "https":
                # 308 keeps the HTTP method (POST stays POST)
                return RedirectResponse(str(request.url.replace(scheme="https")), status_code=308)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if https_mode:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
