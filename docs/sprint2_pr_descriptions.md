# Sprint 2 branches, commits and PR text (Member 1)

Rules: one branch per issue (or the grouped PRs below), the PR says `Closes #N`, the repo owner reviews and merges, and you do not merge your own PR. Merge in the order given because later PRs build on earlier ones.

| Order | Issue(s) | Branch | Files |
|---|---|---|---|
| 1 | MLE-F-025 | `feature/MLE-F-025-save-history` | `models.py`, `services/history.py`, `scripts/seed_history.py`, `tests/conftest.py`, `tests/test_history.py` (TC-025, 025a) |
| 2 | MLE-F-026 + MLE-SEC-003 | `feature/MLE-F-026-view-history` | `routers/history.py` (GET), `main.py`, `frontend/history.html`, `history.js`, `auth.js`; tests for TC-026, 026a, SEC-003 |
| 3 | MLE-F-027 | `feature/MLE-F-027-delete-history` | `routers/history.py` (DELETE), delete button in `history.js`; tests TC-027, 027a, 027b |
| 4 | MLE-SEC-005 | `feature/MLE-SEC-005-rate-limiting` | `ratelimit.py`, `routers/auth.py`, `tests/test_rate_limit.py` |
| 5 | MLE-SEC-004 | `feature/MLE-SEC-004-https` | `config.py`, `middleware.py`, `main.py`, `Dockerfile`, `deploy/`, `.env.example`, `tests/test_security_https.py` |
| 6 | TEST-AUTH | `feature/TEST-AUTH-unit-tests` | `tests/test_auth.py`, `.github/workflows/ci.yml` (coverage gate) |
| 7 | DOCS-S2 | `feature/DOCS-S2-final-docs` | `README.md`, `docs/`, `demo/sprint2_demo.mp4` |

If the routers are one file on your machine, use `git add -p` to commit only the hunks for the issue on each branch. If time is too short, combine PRs 2 and 3 into one and list both issues in it (`Closes #a, closes #b`), and say so in the PR.

Commit commands for each branch:

```
git checkout main && git pull
git checkout -b <branch>
git add <files>
git commit -m "<ISSUE-ID>: <short summary>"
git push -u origin <branch>
```

## PR text

**1. MLE-F-025**
```
Closes #<issue>
## What changed
EvaluationRun and AlgorithmResult models and services/history.save_run. Logged-in runs are stored with the user id; guest runs are stored with user_id NULL and never listed.
## How tested (TC-IDs)
TC-025, TC-025a (pytest)
## Deviation from SRS/SAD/Test Plan?
Yes: guest runs stored in the same table (deviations.md #8)
```

**2. MLE-F-026 + MLE-SEC-003**
```
Closes #<issue>, closes #<issue>
## What changed
GET /history (paged, newest first) and GET /history/{run_id}; all routes require a valid token and take the identity from it. History page in the frontend (text-only rendering, no innerHTML).
## How tested (TC-IDs)
TC-026, TC-026a, TC-SEC-003 (pytest); manual check of history.html
## Deviation from SRS/SAD/Test Plan?
Yes: extra detail route and pagination (deviations.md #6)
```

**3. MLE-F-027**
```
Closes #<issue>
## What changed
DELETE /history/{run_id}: 200 for own runs (results cascade), 403 for other users' or guest runs, 404 for unknown or already deleted. Delete button with confirmation in the UI.
## How tested (TC-IDs)
TC-027, TC-027a, TC-027b (pytest)
## Deviation from SRS/SAD/Test Plan?
No (200 with message is allowed by SADS 4.3)
```

**4. MLE-SEC-005**
```
Closes #<issue>
## What changed
Sliding-window rate limiter on /auth/login (5/min) and /auth/register (10/min) per client IP; 429 with Retry-After; limits configurable by env. X-Forwarded-For is trusted only when TRUST_PROXY=1.
## How tested (TC-IDs)
TC-SEC-005 (pytest, including recovery after the window and header spoofing)
## Deviation from SRS/SAD/Test Plan?
Yes: in-memory limiter (deviations.md #9)
```

**5. MLE-SEC-004**
```
Closes #<issue>
## What changed
ENFORCE_HTTPS mode (308 redirect, HSTS), startup refusal on a weak JWT_SECRET, security headers, Dockerfile, nginx config (TLS 1.2+, HTTP to HTTPS redirect), docker-compose, dev certificate script.
## How tested (TC-IDs)
TC-SEC-004 app-level (pytest). nginx/TLS verified manually with the README table (attach output).
## Deviation from SRS/SAD/Test Plan?
No
```

**6. TEST-AUTH**
```
Closes #<issue>
## What changed
Auth test suite for TC-001 to TC-005c, shared fixtures, and a CI gate that fails under 80% coverage.
## How tested (TC-IDs)
TC-001 to TC-005c (pytest, coverage on app/ above 80%)
## Deviation from SRS/SAD/Test Plan?
No
```

**7. DOCS-S2**
```
Closes #<issue>
## What changed
README, RTM statuses, deviations log, integration notes, Sprint 2 demo video.
## How tested (TC-IDs)
N/A (documentation and recording of merged main)
## Deviation from SRS/SAD/Test Plan?
All deviations listed in docs/deviations.md
```
