# Integration notes for teammates

- **Auth for your endpoints:** `from app.deps import get_current_user, get_optional_user`. Use `get_optional_user` for guest-friendly endpoints (upload, evaluate, reports) and `get_current_user` for login-only ones. Never accept a user id from the request body or query string.
- **Saving history (M3):** call `save_run(...)` from `services/history.py` after metrics are computed (example in README).
- **Rate limiting on other routes:** `dependencies=[Depends(rate_limit("scope", 20))]` from `app/ratelimit.py`.
- **Error envelope (M2, API-ERR):** `main.py` has a 400 handler for validation errors, and routes raise `HTTPException` (`{detail}`). When you add the full `{error:{code,message,request_id}}` envelope, replace the handler and add an `HTTPException` handler; the status codes stay the same, so the tests keep passing apart from the `detail` key checks in `test_auth.py` and `test_rate_limit.py`.
- **Models:** if SETUP-01 already defines `User` and `EvaluationRun`, keep one copy of each. The history code needs the columns listed in `models.py`.
