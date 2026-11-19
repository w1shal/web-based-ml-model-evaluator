# Deliverables audit, 19 November 2026

Baseline: main at 9a2d6b0, including merged PR #111. The review used the three uploaded mini-project deliverable sheets, the evaluation checklist, the repository SRS, SAD and Test Plan, and all 14 open issues.

## Design and sprint evidence

The 12-page SRS defines functional, non-functional and security requirements. The 12-page SAD identifies the components on page 5, the two interactions on pages 9–10, and the error protocol on page 11. The five-page Test Plan maps functional, non-functional and security cases, exceeding the seven-case minimum. Its security tests are in §6.3. The checklist specifically asks for security validation in §5.1. Formal IEEE-format acceptance and visual approval of the diagrams remain for review.

Git history and PR #111 record the delivered workflow. The repository contains the Sprint 1 video and a deviations log. The Sprint 2 video, historical board linkage, per-story estimates and assignments, owner review of each assigned PR, formal sprint freeze, final demonstration and individual viva need team evidence.

## Open issue traceability

| Issue | Implementation or test evidence | Acceptance status |
|---|---|---|
| #28 | Dataset route and rejected-upload tests | Extension and representative disguised binaries rejected with 415 before storage. Plain text may itself be valid single-column CSV. |
| #30 | Dataset API tests | BOM, CRLF, quoted commas, first five rows, missing values and empty/header-only input covered. |
| #31 | ML preprocessing and evaluation API tests | Unknown columns and target/feature overlap rejected. |
| #32 | ConfigurePage, evaluation request schema and workflow tests | Target/features sent to the API. |
| #33 | ML preprocessing, evaluation engine and configuration tests | Median imputation and row drop available. |
| #53 | EvaluatePage and workflow controls | Running status announced and repeat submission disabled. Five-user study, complete keyboard walkthrough and measured contrast outstanding. |
| #56 | Sprint 2 validation checklist | Chrome, Firefox, Edge and tablet signoff outstanding. |
| #57 | Upload route, dataset store and negative API tests | File payload capped at 10 MiB; 1,024 columns and 128 KiB per LF-delimited physical line. Server-generated storage keys. Invalid ownership metadata denies retrieval. |
| #58 | EvaluationRequest and evaluation API tests | Default split 0.2; accepted range 0.05–0.5. |
| #61 | API exception handlers, response header and request logs | Structured errors carry a server-generated request ID. HTTP exceptions retain the existing detail field; rate-limit headers are preserved. |
| #64 | Dataset, preprocessing, ROC-AUC and evaluation tests | Automated invalid-input cases exist; formal D4/D7/D8/D10 fixture equivalence and restart/failure campaign need signoff. |
| #66 | Backend dataset and evaluation tests, frontend upload/configuration and workflow suites | Automated cases executed; test IDs in the formal plan still require individual acceptance review. |
| #67 | Request middleware and log-capture regression | Application request log records ID and status only. Production proxy and server logging require separate inspection. |
| #70 | Corrected setup guide, deviations update and reports | Automated evidence committed; Sprint 2 video and final approval outstanding. |

## Test Plan addendum

TC-007 and TC-SEC-002 now include wrong extension, disguised binary/document, excess bytes, column count and physical-line length. Each case checks the response and that the dataset directory stays empty. Ownership tests cover damaged and missing metadata. TC-API-02 checks log correlation and distinct IDs for equivalent authentication failures. Frontend regression checks exercise the filename in the preview heading and the formatted history percentage.

## Execution evidence

- [Unit test results](reports/unit-tests.md)
- [System validation results](reports/system-validation.md)
- [Line coverage](reports/code-coverage.md)
- [Branch coverage](reports/branch-coverage.md)

The application suite uses temporary datasets and SQLite. Real-browser parity, a clean Docker host, staging TLS, the five-person usability exercise, authenticated deployment logs and guest isolation between different anonymous browsers require further validation. Guest resources currently rely on possession of their generated IDs. An automated pass alone does not satisfy the Test Plan's exit criteria.
