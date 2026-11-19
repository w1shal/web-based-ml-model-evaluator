# Deliverables audit, 19 November 2026

Baseline: main at 9a2d6b0, including merged PR #111. The review used the three uploaded mini-project deliverable sheets, the evaluation checklist, the repository SRS, SAD and Test Plan, and all 14 open issues.

## Design and sprint evidence

The [user-workflow use-case diagram](SRS/evaluator-use-cases.svg) accompanies SRS §8.1. The [Test Plan §5.1 addendum](Test-Plan/sprint-2-security-validation.md) maps each security case to its validation evidence.

The 12-page SRS defines functional, non-functional and security requirements. The 12-page SAD identifies the components on page 5, the two interactions on pages 9–10, and the error protocol on page 11. The five-page Test Plan maps functional, non-functional and security cases, exceeding the seven-case minimum. Its security tests are in §6.3. The checklist specifically asks for security validation in §5.1. Formal IEEE-format acceptance and visual approval of the diagrams remain for review.

Git history and PR #111 record the delivered workflow. The repository contains the Sprint 1 video, [Sprint 2 recording](../demo/sprint-2-demo.mp4) and deviations log. Historical board linkage, per-story estimates and assignments, owner review of each assigned PR, formal sprint freeze, final demonstration and individual viva need team evidence.

## Open issue traceability

The SRS identifiers below cover the full set of application requirements, including work delivered before PR #111. Test filenames refer to backend/tests or frontend/src/test.

| SRS identifiers | Implementation | Verification and limits |
|---|---|---|
| MLE-F-001–005 | Authentication router, bcrypt, JWT verification and revocation | Registration, login, security and logout suites passed. |
| MLE-F-006–009 | Upload route and UploadPage | Dataset API and upload component tests cover rejection before storage, the inclusive file-size limit, preview and warnings. |
| MLE-F-010–012 | ConfigurePage and ML preprocessing | Configuration, categorical preprocessing and evaluation suites passed. |
| MLE-F-013–016 | Algorithm registry, selection, evaluation schema and engine | Registry, built-in models, selection and evaluation suites passed. |
| MLE-F-017–019 | ML metrics, confusion matrix and ROC-AUC | Reference metrics, averaging, matrix and ROC-AUC suites passed. |
| MLE-F-020–022 | ResultsPage chart, matrix and sortable comparison | ResultsPage tests passed. |
| MLE-F-023–024 | Report router and download controls | Report API and results component tests passed. |
| MLE-F-025–027 | History service, owner checks, HistoryPage | History service, API and component suites passed. |
| MLE-NF-001, 003, 006 | ML engine, concurrency gate and registry | Performance, concurrency/persistence and modularity suites passed locally. Multi-worker deployment still needs validation. |
| MLE-NF-002, 004, 005 | Workflow UI, error handlers and client | Automated workflow and invalid-input cases passed. The timing study, formal reliability campaign and latest-two-version browser matrix remain separate acceptance criteria. |
| MLE-SEC-001–003 | Password hashing, upload validation and resource ownership | Security, dataset and history suites passed. Anonymous resource IDs have bearer semantics. |
| MLE-SEC-004–006 | HTTPS middleware, reverse proxy, rate limiter and request logging | Local HTTPS/rate-limit and request-correlation tests passed. Staging TLS and production log review are pending. |

| Issue | Implementation or test evidence | Acceptance status |
|---|---|---|
| #28 | Dataset route and rejected-upload tests | Extension and representative disguised binaries rejected with 415 before storage. Plain text may itself be valid single-column CSV. |
| #30 | Dataset API tests | BOM, CRLF, quoted commas, first five rows, missing values and empty/header-only input covered. |
| #31 | ML preprocessing and evaluation API tests | Unknown columns and target/feature overlap rejected. |
| #32 | ConfigurePage, evaluation request schema and workflow tests | Target/features sent to the API. |
| #33 | ML preprocessing, evaluation engine and configuration tests | Median imputation and row drop available. |
| #53 | EvaluatePage and workflow controls | Running status announced and repeat submission disabled. Five-user study, complete keyboard walkthrough and measured contrast outstanding. |
| #56 | [Sprint 2 browser runs](sprint-2-validation.md) | Live workflow passed in three desktop browsers and a tablet viewport. Second browser versions and manual visual checks remain open. |
| #57 | Upload route, dataset store and negative API tests | File payload capped at 10 MiB; 1,024 columns and 128 KiB per LF-delimited physical line. Server-generated storage keys. Invalid ownership metadata denies retrieval. |
| #58 | EvaluationRequest and evaluation API tests | Default split 0.2; accepted range 0.05–0.5. |
| #61 | API exception handlers, response header and request logs | Structured errors carry a server-generated request ID. HTTP exceptions retain the existing detail field; rate-limit headers are preserved. |
| #64 | Dataset, preprocessing, ROC-AUC and evaluation tests | Automated invalid-input cases exist; formal D4/D7/D8/D10 fixture equivalence and restart/failure campaign need signoff. |
| #66 | Backend dataset and evaluation tests, frontend upload/configuration and workflow suites | Automated cases executed; test IDs in the formal plan still require individual acceptance review. |
| #67 | Request middleware and log-capture regression | Application request log records ID and status only. Production proxy and server logging require separate inspection. |
| #70 | Corrected setup guide, deviations update, reports and Sprint 2 recording | Application evidence available. Team review and final approval outstanding. |

## Test Plan addendum

TC-007 and TC-SEC-002 include wrong extension, disguised binary/document, excess bytes, column count and physical-line length. TC-007a exercises the exact 10 MiB boundary and one byte above it. TC-008 covers ragged rows and duplicate headers as well as empty/header-only input. Each new rejection case checks the response and that the dataset directory stays empty. Ownership tests cover damaged and missing metadata. TC-API-02 checks log correlation and distinct IDs for equivalent authentication failures. Frontend regression checks exercise the filename in the preview heading and the formatted history percentage.

## Execution evidence

- [Unit test results](reports/unit-tests.md)
- [System validation results](reports/system-validation.md)
- [Line coverage](reports/code-coverage.md)
- [Branch coverage](reports/branch-coverage.md)

The application suite uses temporary datasets and SQLite. GitHub Actions built and smoke-tested the Docker image on a hosted runner. The live browser checks below cover one version per browser. Staging TLS, the five-person usability exercise, deployment logs and guest isolation between different anonymous browsers require further validation. Guest resources currently rely on possession of their generated IDs. An automated pass alone does not satisfy the Test Plan's exit criteria.

See the [browser validation record](sprint-2-validation.md) and the [CI run for the application changes](https://github.com/w1shal/web-based-ml-model-evaluator/actions/runs/44460829106).
