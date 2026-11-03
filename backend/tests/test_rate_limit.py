from app.ratelimit import limiter
from tests.conftest import GOOD


def bad_login(c, headers=None):
    return c.post("/auth/login", json={"identifier": "nobody", "password": "wrongpass1"}, headers=headers or {})


def test_login_rate_limited_then_recovers(client, monkeypatch):                # TC-SEC-005
    monkeypatch.setenv("RATE_LIMIT_LOGIN_MAX", "3")
    monkeypatch.setenv("RATE_LIMIT_WINDOW", "60")
    now = [1000.0]
    limiter.clock = lambda: now[0]
    assert [bad_login(client).status_code for _ in range(3)] == [401, 401, 401]
    r = bad_login(client)
    assert r.status_code == 429 and int(r.headers["Retry-After"]) >= 1
    now[0] += 61                                  # window passes
    assert bad_login(client).status_code == 401   # legitimate access recovers


def test_register_rate_limited_separately(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REGISTER_MAX", "2")
    codes = []
    for n in range(3):
        codes.append(client.post("/auth/register", json={**GOOD, "username": f"user{n}",
                                                         "email": f"u{n}@example.com"}).status_code)
    assert codes == [201, 201, 429]
    assert bad_login(client).status_code == 401   # login counter is independent


def test_limit_is_per_client_ip_when_proxy_trusted(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_MAX", "2")
    monkeypatch.setenv("TRUST_PROXY", "1")
    ip_a, ip_b = {"X-Forwarded-For": "10.0.0.1"}, {"X-Forwarded-For": "10.0.0.2"}
    assert [bad_login(client, ip_a).status_code for _ in range(3)] == [401, 401, 429]
    assert bad_login(client, ip_b).status_code == 401


def test_forwarded_header_ignored_when_proxy_not_trusted(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_MAX", "2")
    codes = [bad_login(client, {"X-Forwarded-For": f"10.0.0.{n}"}).status_code for n in range(3)]
    assert codes == [401, 401, 429]               # spoofing the header does not bypass the limit
