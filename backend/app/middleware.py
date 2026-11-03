"""HTTPS enforcement and baseline response security headers."""

from fastapi import Request
from fastapi.responses import RedirectResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .config import enforce_https, trust_proxy


def _request_scheme(request: Request) -> str:
    """Resolve the external scheme without trusting client-supplied headers by default."""
    if trust_proxy():
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto:
            return forwarded_proto.split(",", 1)[0].strip().lower()
    return request.url.scheme.lower()


def _add_security_headers(response: Response, *, is_https: bool) -> None:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if is_https:
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000",
        )


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        external_scheme = _request_scheme(request)
        https_required = enforce_https()

        if https_required and external_scheme != "https":
            response = RedirectResponse(
                url=str(request.url.replace(scheme="https")),
                status_code=308,
            )
            _add_security_headers(response, is_https=False)
            return response

        response = await call_next(request)
        _add_security_headers(
            response,
            is_https=https_required and external_scheme == "https",
        )
        return response
