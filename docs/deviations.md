# Sprint 1 Deviations Log

**Review date:** 2026-10-29
**Status:** Draft for teammate review

## D-01: Evaluation workflow is not yet end-to-end

**Relevant SRS requirement area:** Functional requirements covering dataset upload, evaluation configuration, evaluation execution, and results reporting.

**Relevant SAD design area:** The frontend workflow consisting of Upload, Configure, Evaluate, and Results, including frontend-to-backend integration.

**Expected behavior:** Users should be able to progress through the evaluation workflow and obtain results to the extent specified in the requirements.

**Current implementation:** The frontend displays the four workflow stages, but they are currently a scaffold. Dataset upload, evaluation configuration, execution, and results generation are not yet integrated into this frontend workflow. The application does have a working registration and login interface, JWT-based session verification, logout, and guest entry.

**Reason:** The current implementation has established the authentication flow and frontend structure, while the end-to-end evaluation workflow remains incomplete.

**Follow-up action:** Complete and integrate the missing evaluation stages with the responsible team members. Add relevant integration tests and update the demo when those features become available.

**Demo disclosure:** The four workflow stages must be presented as a scaffold, not as implemented evaluation functionality.

## Review notes

- Verify the exact SRS and SAD section numbers against the source documents before final approval.
- Review this log with a teammate and add any other confirmed deviations.
- Do not describe incomplete functionality as implemented.
- Ensure the demo contains no passwords, access tokens, API secrets, or private user data.
