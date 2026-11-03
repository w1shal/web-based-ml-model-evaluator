# Web Based ML Model Evaluator: Sprint 2 (Member 1: Auth, History, Security, Docs)

This package holds Member 1's Sprint 2 work (PES2UG24CS599) as a drop-in project folder. It includes the Sprint 1 auth code (updated) so everything runs and tests standalone. Merge the files into the team repo; where a file already exists (`main.py`, `models.py`, `db.py`), merge by hand and keep your teammates' additions.

## What is here

| Issue | Pts | Where |
|---|---|---|
| MLE-F-025 Save history | 3 | `services/history.py` (`save_run`), `models.py` (EvaluationRun, AlgorithmResult) |
| MLE-F-026 View own history | 3 | `routers/history.py` (GET), `frontend/history.html`, `history.js` |
| MLE-F-027 Delete own history | 2 | `routers/history.py` (DELETE), history UI delete button |
| MLE-SEC-003 Auth required for history | 2 | `routers/history.py` (every route uses `get_current_user`) |
| MLE-SEC-005 Rate limiting | 3 | `ratelimit.py`, used in `routers/auth.py` |
| MLE-SEC-004 HTTPS/TLS | 2 | `middleware.py`, `config.py`, `deploy/`, `Dockerfile`, `.env.example` |
| TEST-AUTH Tests | 3 | `backend/tests/` (41 tests, 96% coverage on `app/`) |
| DOCS-S2 Docs and video | 3 | `README.md`, `docs/` |

## Run it

```bash
pip install -r requirements.txt
cd backend
pytest --cov=app                      # all tests
uvicorn app.main:app --reload         # API on http://localhost:8000 (docs at /docs)
python scripts/seed_history.py        # optional: demo user "demo" / "Demo12345" with 2 saved runs
```

Frontend: open `frontend/auth.html` (login) and `frontend/history.html` (history). Serve the folder with any static server, for example `python -m http.server 3000 --directory frontend`. The default CORS list allows `localhost:3000` and `localhost:5173`; set `CORS_ORIGINS` for other ports.

## API added in Sprint 2

| Method and path | Auth | Result |
|---|---|---|
| GET `/history?limit=50&offset=0` | Yes | 200 `{items, total, limit, offset}`; only the caller's runs, newest first |
| GET `/history/{run_id}` | Yes | 200 run detail with confusion matrices; 403 if not yours; 404 if unknown |
| DELETE `/history/{run_id}` | Yes | 200 `{message}`; run and its results removed; 403 / 404 as above |
| POST `/auth/login`, `/auth/register` | No | Now rate limited: 429 with `Retry-After` after the threshold |

No token or an invalid, expired or revoked token returns 401 on all history routes.

## Hooking history into POST /evaluations (Member 3)

After the metrics are computed, add these lines to the evaluation endpoint. The user comes from the optional-auth dependency, so guests still work:

```python
from ..deps import get_optional_user
from ..services.history import save_run

# in the endpoint signature:  user = Depends(get_optional_user), db = Depends(get_db)
run = save_run(db, user.user_id if user else None,
               dataset_name=dataset.name, target_column=cfg.target_column,
               feature_columns=cfg.feature_columns, split_ratio=cfg.test_size,
               results=results)          # list of dicts, SADS 4.3.2 item shape
# return run.run_id in the response
```

A guest run (`user_id=None`) is stored for the guest flow but never listed in anyone's history (TC-025a).

## Configuration (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `JWT_SECRET` | dev value | Required (32+ chars) when `ENFORCE_HTTPS=1`; the app refuses to start otherwise |
| `DATABASE_URL` | `sqlite:///./app.db` | SQLite for dev; a PostgreSQL URL for staging |
| `ENFORCE_HTTPS` | 0 | 1 = redirect HTTP to HTTPS (308) and send HSTS |
| `TRUST_PROXY` | 0 | 1 = use the first `X-Forwarded-For` entry as client IP (only behind nginx) |
| `RATE_LIMIT_LOGIN_MAX` / `RATE_LIMIT_REGISTER_MAX` | 5 / 10 | Attempts per window per client IP |
| `RATE_LIMIT_WINDOW` | 60 | Window in seconds |
| `CORS_ORIGINS` | localhost:3000, 5173 | Comma-separated allowed origins |

The rate limiter is in memory and per process. That is fine for one container. For several workers, move the counters to Redis.

## HTTPS deployment and how to verify TC-SEC-004

```bash
sh deploy/gen-dev-cert.sh                  # self-signed cert (use a real one in production)
cp .env.example .env                       # set JWT_SECRET
docker compose -f deploy/docker-compose.yml --env-file .env up --build
```

When serving through nginx, add `<script>window.API_BASE = ""</script>` before the page scripts so the frontend calls the same origin.

| Check | Command | Expected |
|---|---|---|
| HTTP redirected | `curl -I http://localhost/` | 301 to `https://` |
| TLS 1.2 works | `openssl s_client -connect localhost:443 -tls1_2 </dev/null` | handshake succeeds |
| TLS 1.1 refused | `openssl s_client -connect localhost:443 -tls1_1 </dev/null` | handshake failure |
| HSTS present | `curl -kI https://localhost/auth/me` | `Strict-Transport-Security` header |

## Testing status

- Python code: 41 pytest tests pass, 96% coverage on `app/` (plus a live uvicorn smoke test: seed, login, history, 401, 429, HTTPS-mode redirect, weak-secret refusal).
- Not executed here: the Docker, nginx and TLS files (no Docker in the build environment). Run the verification table above on your machine and record the results before the freeze.
- Frontend history page: syntax-checked only; try it in a browser against the seeded demo user.
