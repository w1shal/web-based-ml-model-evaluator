import pytest

from app.ratelimit import _positive_int_env, limiter
from tests.conftest import GOOD


def bad_login(client, headers=None):
    return client.post(
        "/auth/login",
        json={"identifier": "unknown-user", "password": "Wrong123pw"},
        headers=headers or {},
    )


def test_login_rate_limited_then_recovers(client, monkeypatch):
    """Login is blocked after the configured threshold and recovers after the window."""
    monkeypatch.setenv("RATE_LIMIT_LOGIN_MAX", "3")
    monkeypatch.setenv("RATE_LIMIT_WINDOW", "60")

    now = [1000.0]
    limiter.clock = lambda: now[0]

    assert [bad_login(client).status_code for _ in range(3)] == [401, 401, 401]

    response = bad_login(client)
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many requests. Please try again later."
    assert int(response.headers["Retry-After"]) >= 1

    now[0] += 61
    assert bad_login(client).status_code == 401


def test_register_rate_limited_separately(client, monkeypatch):
    """Registration has its own independently configurable limit."""
    monkeypatch.setenv("RATE_LIMIT_REGISTER_MAX", "2")

    codes = []
    for number in range(3):
        response = client.post(
            "/auth/register",
            json={
                **GOOD,
                "username": f"rate-user-{number}",
                "email": f"rate-user-{number}@example.com",
            },
        )
        codes.append(response.status_code)

    assert codes == [201, 201, 429]
    # Login has a separate scope and remains available.
    assert bad_login(client).status_code == 401


def test_limit_is_per_forwarded_client_ip_when_proxy_trusted(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_MAX", "2")
    monkeypatch.setenv("TRUST_PROXY", "1")

    ip_a = {"X-Forwarded-For": "10.0.0.1"}
    ip_b = {"X-Forwarded-For": "10.0.0.2"}

    assert [bad_login(client, ip_a).status_code for _ in range(3)] == [
        401, 401, 429
    ]
    assert bad_login(client, ip_b).status_code == 401


def test_forwarded_header_ignored_when_proxy_not_trusted(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_MAX", "2")
    monkeypatch.delenv("TRUST_PROXY", raising=False)

    codes = [
        bad_login(
            client,
            {"X-Forwarded-For": f"10.0.0.{number}"},
        ).status_code
        for number in range(3)
    ]
    assert codes == [401, 401, 429]


@pytest.mark.parametrize("raw", ["0", "-1", "invalid"])
def test_rate_limit_configuration_must_be_positive(monkeypatch, raw):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_MAX", raw)
    with pytest.raises(RuntimeError, match="must be a positive integer"):
        _positive_int_env("RATE_LIMIT_LOGIN_MAX", 5)
