from datetime import datetime, timedelta, timezone

import jwt

from app.models import AlgorithmResult, EvaluationRun
from app.security import ALGO, SECRET, create_token
from tests.conftest import SAMPLE_RESULTS


def test_authenticated_run_is_linked_to_user(client, make_user, make_run, session_factory):   # TC-025
    u = make_user("alice")
    run_id = make_run(u["user_id"])
    with session_factory() as db:
        assert db.get(EvaluationRun, run_id).user_id == u["user_id"]
    items = client.get("/history", headers=u["headers"]).json()["items"]
    assert [i["run_id"] for i in items] == [run_id]


def test_saved_metadata(client, make_user, make_run):                                          # MLE-F-025
    u = make_user("alice")
    make_run(u["user_id"], dataset="breast_cancer.csv")
    item = client.get("/history", headers=u["headers"]).json()["items"][0]
    assert item["dataset_name"] == "breast_cancer.csv"
    assert item["algorithms"] == ["random_forest", "logistic_regression"]
    assert item["timestamp"].endswith("Z")
    assert item["metrics"][0]["accuracy"] == SAMPLE_RESULTS[0]["accuracy"]


def test_guest_run_not_in_history(client, make_user, make_run):                                # TC-025a
    u = make_user("alice")
    make_run(None, dataset="guest.csv")
    body = client.get("/history", headers=u["headers"]).json()
    assert body["items"] == [] and body["total"] == 0


def test_list_only_own_runs_newest_first(client, make_user, make_run):                        # TC-026
    a, b = make_user("alice"), make_user("bob")
    base = datetime(2026, 10, 1, 12, 0, 0)
    r1 = make_run(a["user_id"], dataset="one.csv", timestamp=base)
    r2 = make_run(a["user_id"], dataset="two.csv", timestamp=base + timedelta(minutes=5))
    r3 = make_run(a["user_id"], dataset="three.csv", timestamp=base + timedelta(minutes=9))
    rb = make_run(b["user_id"], dataset="bobs.csv")
    ids = [i["run_id"] for i in client.get("/history", headers=a["headers"]).json()["items"]]
    assert ids == [r3, r2, r1] and rb not in ids


def test_history_requires_authentication(client):                                              # TC-026a / MLE-SEC-003
    missing = client.get("/history")
    malformed = client.get("/history", headers={"Authorization": "Bearer not.a.token"})
    assert missing.status_code == malformed.status_code == 401
    assert missing.headers.get("www-authenticate") == "Bearer"
    assert client.get("/history/run_x").status_code == 401
    assert client.delete("/history/run_x").status_code == 401


def test_history_rejects_expired_invalid_signature_and_malformed_claims(client):                 # MLE-SEC-003
    now = datetime.now(timezone.utc)
    expired = create_token(1, minutes=-1)

    valid = create_token(1)
    parts = valid.split(".")
    signature = parts[2]
    tampered_signature = ("A" if signature[0] != "A" else "B") + signature[1:]
    invalid_signature = ".".join([parts[0], parts[1], tampered_signature])

    # A correctly signed JWT missing jti must still be rejected as an invalid token (401).
    missing_jti = jwt.encode(
        {"sub": "1", "iat": now, "exp": now + timedelta(minutes=5)},
        SECRET,
        algorithm=ALGO,
    )
    # A signed but non-numeric subject must not escape as a ValueError/500.
    invalid_subject = jwt.encode(
        {"sub": "not-a-user-id", "jti": "test-jti", "iat": now,
         "exp": now + timedelta(minutes=5)},
        SECRET,
        algorithm=ALGO,
    )

    for token in (expired, invalid_signature, missing_jti, invalid_subject):
        response = client.get("/history", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.headers.get("www-authenticate") == "Bearer"


def test_revoked_token_cannot_read_history(client, make_user):
    u = make_user("alice")
    client.post("/auth/logout", headers=u["headers"])
    assert client.get("/history", headers=u["headers"]).status_code == 401


def test_identity_comes_from_token_not_client(client, make_user, make_run):                    # TC-SEC-003
    a, b = make_user("alice"), make_user("bob")
    make_run(a["user_id"], dataset="alice.csv")
    rb = make_run(b["user_id"], dataset="bob.csv")
    r = client.get(f"/history?user_id={b['user_id']}", headers=a["headers"])
    assert r.status_code == 200
    ids = [i["run_id"] for i in r.json()["items"]]
    assert rb not in ids and len(ids) == 1


def test_pagination(client, make_user, make_run):
    u = make_user("alice")
    base = datetime(2026, 10, 1)
    for n in range(5):
        make_run(u["user_id"], dataset=f"d{n}.csv", timestamp=base + timedelta(minutes=n))
    page = client.get("/history?limit=2&offset=2", headers=u["headers"]).json()
    assert page["total"] == 5 and [i["dataset_name"] for i in page["items"]] == ["d2.csv", "d1.csv"]
    assert client.get("/history?limit=0", headers=u["headers"]).status_code == 400


def test_view_own_run_detail(client, make_user, make_run):
    u = make_user("alice")
    run_id = make_run(u["user_id"])
    d = client.get(f"/history/{run_id}", headers=u["headers"]).json()
    assert d["target_column"] == "species" and d["split_ratio"] == 0.2
    assert d["confusion_matrices"]["random_forest"] == [[45, 5], [4, 46]]


def test_view_other_users_run_forbidden(client, make_user, make_run):
    a, b = make_user("alice"), make_user("bob")
    run_id = make_run(a["user_id"])
    assert client.get(f"/history/{run_id}", headers=b["headers"]).status_code == 403
    assert client.get("/history/run_missing", headers=b["headers"]).status_code == 404


def test_delete_own_run_removes_dependents(client, make_user, make_run, session_factory):    # TC-027
    u = make_user("alice")
    run_id = make_run(u["user_id"])
    assert client.delete(f"/history/{run_id}", headers=u["headers"]).status_code == 200
    with session_factory() as db:
        assert db.get(EvaluationRun, run_id) is None
        assert db.query(AlgorithmResult).count() == 0
    assert client.get(f"/history/{run_id}", headers=u["headers"]).status_code == 404
    assert client.get("/history", headers=u["headers"]).json()["items"] == []


def test_delete_other_users_run_forbidden(client, make_user, make_run, session_factory):     # TC-027a
    a, b = make_user("alice"), make_user("bob")
    run_id = make_run(a["user_id"])
    assert client.delete(f"/history/{run_id}", headers=b["headers"]).status_code == 403
    with session_factory() as db:
        assert db.get(EvaluationRun, run_id) is not None
        assert db.query(AlgorithmResult).count() == 2
    assert len(client.get("/history", headers=a["headers"]).json()["items"]) == 1


def test_delete_guest_run_forbidden(client, make_user, make_run):
    u = make_user("alice")
    run_id = make_run(None)
    assert client.delete(f"/history/{run_id}", headers=u["headers"]).status_code == 403


def test_delete_twice_or_unknown_is_404(client, make_user, make_run):                         # TC-027b
    u = make_user("alice")
    run_id = make_run(u["user_id"])
    assert client.delete(f"/history/{run_id}", headers=u["headers"]).status_code == 200
    assert client.delete(f"/history/{run_id}", headers=u["headers"]).status_code == 404
    assert client.delete("/history/run_unknown", headers=u["headers"]).status_code == 404
