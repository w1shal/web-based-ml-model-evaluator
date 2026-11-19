# Sprint 2 Test Plan addendum

## 5.1 Security validation

This supplement cross-references the original plan's §6.3 security cases. The submitted PDF retains its original section numbering.

| Case | Stimulus and expected outcome | Evidence |
|---|---|---|
| TC-SEC-001 | Register and inspect stored credentials. A salted bcrypt hash is stored. Invalid logins receive equivalent messages. | Registration, security and login suites |
| TC-SEC-002 | Submit invalid extensions, binary content, oversize, ragged, duplicate-header and excessive-width input. Reject the request before dataset persistence. Escape formula-leading cells when exporting CSV. | Dataset API and reports suites |
| TC-SEC-003 | Request another account's datasets, history and reports. Deny access. Missing or corrupt ownership metadata also denies dataset access. | History, evaluation, reports and dataset-store suites |
| TC-SEC-004 | With HTTPS enforcement enabled, send an HTTP request and inspect the redirect and HTTPS response headers. | Local security middleware tests. Staging handshake and protocol negotiation pending. |
| TC-SEC-005 | Exceed configured authentication request limits. Expect 429 and a retry interval. | Rate-limit suite |
| TC-SEC-006 | Submit a sentinel dataset value and inspect captured request logs. Check request ID correlation and absence of the value. | Dataset API log-capture regression. Deployment log inspection pending. |

Execution evidence is in the [system validation report](../reports/system-validation.md).
