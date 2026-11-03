# Deviations from SRS v1.0, SADS v1.0 and Test Plan v1.0

Explain these during the final demo. Add rows for any change your teammates made.

| # | Sprint | Area | Documented | Implemented | Reason |
|---|---|---|---|---|---|
| 1 | 1 | Login (MLE-F-003) | Username/email and password | One `identifier` field accepts username or email | Simpler UI; same requirement |
| 2 | 1 | Logout (MLE-F-005) | Invalidate token | Server-side blocklist of token ids (jti) | JWTs cannot be revoked otherwise |
| 3 | 1 | Registration errors | 400/409 | 409 duplicate, 400 invalid fields | Matches Test Plan |
| 4 | 1 | Password rules | "Strong password" | 8 to 72 chars, letters and digits | bcrypt input limit is 72 bytes |
| 5 | 1 | Logout status | 200 or 204 | 200 `{message}` | Allowed by SADS 4.3 |
| 6 | 2 | History routes (SADS 4.3) | `GET /history`, `DELETE /history/{id}` | Added `GET /history/{run_id}` for run detail; list supports `limit`/`offset` and returns `total` | Needed for "view previous runs" in the UI |
| 7 | 2 | Delete status | 204 or 200 | 200 `{message}` | Consistent with logout |
| 8 | 2 | Guest runs (SADS open issue) | Short-lived storage, signed refs or in-memory | Stored in the same table with `user_id = NULL`, excluded from history | Simplest option that satisfies TC-025a; add a cleanup job if time allows |
| 9 | 2 | Rate limiting (MLE-SEC-005) | Threshold on auth endpoints | In-memory sliding window per client IP (login 5/min, register 10/min, configurable) | Single-container deployment; Redis needed for multiple workers |
| 10 | 2 | HTTPS (MLE-SEC-004) | TLS 1.2+ | nginx terminates TLS (1.2 and 1.3) and redirects HTTP; app also redirects (308) and sends HSTS when `ENFORCE_HTTPS=1` | Defence in depth |
| 11 | 2 | Error envelope (SADS 4.4) | `{error:{code,message,request_id}}` everywhere | Auth/history routes return `{detail}` until API-ERR (M2) is merged | See `INTEGRATION.md` |
| 12 | 2 | Startup | Tables created at import | Tables created in the FastAPI startup (lifespan) | Avoids creating a database file during tests |
