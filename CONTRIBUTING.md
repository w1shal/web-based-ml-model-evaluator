
# Contributing Guide

## Branch Naming
Create a separate branch for each issue. Use one of these formats:
- `feature/ISSUE_NUMBER-short-description`
- `fix/ISSUE_NUMBER-short-description`
- `chore/ISSUE_NUMBER-short-description`

Example: `chore/1-ci-pr-workflow`

## Pull Request Process
1. Link every implementation PR to its GitHub issue using `Closes #ISSUE_NUMBER`.
2. Complete the pull request template, including summary, tests, evidence, and SRS requirement IDs.
3. Run the relevant tests and check that GitHub Actions passes.
4. Request review from the repository owner.
5. Address review comments and wait for approval before merging.
6. Merge only after required checks pass.

## Review and Main Branch
Do not push changes directly to `main`.
Use a pull request for all changes. The repository owner should configure branch protection, required approvals, and CI status checks where supported.

## Running Tests, Lint and Coverage
CI runs all of these on every push and pull request. Run them locally before opening a PR.

### Backend (from the repository root)
```bash
pip install -r requirements.txt ruff
ruff check backend tests                 # lint (rules configured in pyproject.toml)
ruff check backend tests --fix           # auto-fix safe lint issues

cd backend
python -m pytest -m unit                 # unit tests: one module at a time, no HTTP/DB
python -m pytest -m integration          # integration tests: API + DB + ML engine together
python -m pytest -m "not performance" --cov --cov-report=term-missing --cov-report=html
                                         # full suite + coverage (fails below 90%, see backend/.coveragerc)
python -m pytest -m performance          # optional timing benchmarks (not run in CI)
```
Tests are tagged `unit` or `integration` automatically (see `backend/tests/conftest.py`):
anything in `tests/integration/` or that uses the `client`/database fixtures is an integration test.
New isolated tests go in `backend/tests/unit/`, new end-to-end API tests in `backend/tests/integration/`.

### Frontend (from `frontend/`)
```bash
npm ci
npm run lint            # oxlint
npm run typecheck       # tsc
npm test                # vitest
npm run test:coverage   # vitest + v8 coverage (thresholds in vite.config.ts), HTML report in coverage/
```
