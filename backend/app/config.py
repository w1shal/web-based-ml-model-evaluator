"""Environment-based configuration for deployment security."""

import os


INSECURE_SECRET_VALUES = {"", "dev-only-change-me", "change-me"}


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def enforce_https() -> bool:
    return env_bool("ENFORCE_HTTPS")


def trust_proxy() -> bool:
    return env_bool("TRUST_PROXY")


def cors_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def validate_production_config() -> None:
    """Reject HTTPS-enforced deployments with missing or weak JWT secrets."""
    if not enforce_https():
        return

    secret = os.getenv("JWT_SECRET", "")
    if (
        secret in INSECURE_SECRET_VALUES
        or len(secret.encode("utf-8")) < 32
    ):
        raise RuntimeError(
            "JWT_SECRET must be set to a random value of at least 32 bytes "
            "when ENFORCE_HTTPS=1"
        )
