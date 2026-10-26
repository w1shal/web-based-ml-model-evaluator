
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
