"""Environment-based configuration (MLE-SEC-004: secrets come from the environment)."""
import os

DEFAULT_SECRET = "dev-only-change-me"


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0").strip().lower() in ("1", "true", "yes", "on")


def enforce_https() -> bool:
    return env_bool("ENFORCE_HTTPS")


def trust_proxy() -> bool:
    return env_bool("TRUST_PROXY")


def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


def validate_production_config() -> None:
    """Refuse to start in HTTPS-enforced (deployed) mode with a weak or default JWT secret."""
    if not enforce_https():
        return
    secret = os.getenv("JWT_SECRET", "")
    if secret in ("", DEFAULT_SECRET) or len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET must be set to a random value of at least 32 characters when ENFORCE_HTTPS=1"
        )
