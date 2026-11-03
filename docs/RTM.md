# Requirements Traceability Matrix: status at Sprint 2

Status "Pass" means the listed test cases are automated and passing (pytest, 41 tests). "Check" means the owner must confirm before the freeze. Fill in the Check rows with your teammates' results.

| Req ID | Requirement | Design element | Test cases | Owner | Status |
|---|---|---|---|---|---|
| MLE-F-001 | User registration | Auth module | TC-001, 005a, 005b | M1 | Pass |
| MLE-F-002 | Password hashing | Auth module | TC-002 | M1 | Pass |
| MLE-F-003 | User login | Auth module | TC-003, 005c | M1 | Pass |
| MLE-F-004 | Generic invalid-login error | Auth module | TC-005 | M1 | Pass |
| MLE-F-005 | Logout and token invalidation | Auth module | TC-004 | M1 | Pass |
| MLE-F-006 to 009 | Upload, validation, preview | Upload module | TC-006 to 009c | M2 | Check |
| MLE-F-010 to 012 | Target, features, missing values | Config module | TC-010 to 012 | M2 | Check |
| MLE-F-013 to 015 | Algorithms, multi-select, split | Evaluation engine / Config | TC-013 to 015a | M3 / M2 | Check |
| MLE-F-016 to 019 | Train, metrics, confusion matrix, ROC-AUC | Evaluation engine | TC-016 to 019f | M3 | Check |
| MLE-F-020 to 022 | Charts, heatmap, sortable table | Frontend dashboard | TC-020 to 022a | M4 | Check |
| MLE-F-023, 024 | PDF and CSV export | Report module | TC-023 to 024c | M4 | Check |
| MLE-F-025 | Save history | History module | TC-025, 025a | M1 | Pass |
| MLE-F-026 | View own history | History module | TC-026, 026a | M1 | Pass |
| MLE-F-027 | Delete own history | History module | TC-027, 027a, 027b | M1 | Pass |
| MLE-NF-001 | Performance (10k x 50 in 15 s) | Evaluation engine | TC-N01 | M3 | Check |
| MLE-NF-002 | Usability | Frontend | TC-N02 | M4 | Check |
| MLE-NF-003 | 20 concurrent evaluations | Backend | TC-N03 | M3 | Check |
| MLE-NF-004 | Reliability on invalid input | Upload / API | TC-008, 019c | M2 | Check |
| MLE-NF-005 | Cross-browser | Frontend | TC-N05 | M4 | Check |
| MLE-NF-006 | Modularity | Evaluation engine | TC-015a, N06 | M3 | Check |
| MLE-SEC-001 | bcrypt with unique salt | Auth module | TC-SEC-001 | M1 | Pass |
| MLE-SEC-002 | Upload validation | Upload module | TC-SEC-002, 007, 008 | M2 | Check |
| MLE-SEC-003 | History access control | History / Auth | TC-SEC-003, 026a, 027a | M1 | Pass |
| MLE-SEC-004 | HTTPS/TLS | Infrastructure | TC-SEC-004 | M1 | App-level Pass; nginx/TLS Check (run the README verification table) |
| MLE-SEC-005 | Login/register rate limiting | Auth module | TC-SEC-005 | M1 | Pass |
