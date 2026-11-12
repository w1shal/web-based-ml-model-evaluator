# Evaluation history integration contract

This document defines the history persistence integration point for the evaluator endpoint tracked by issue #43.

## Required integration point

After the evaluation engine has completed all selected algorithms and constructed the result fields, the POST /evaluations handler must call:

    from ..deps import get_optional_user
    from ..services.history import persist_completed_evaluation

    # current_user is resolved from the Bearer token and is None for guests.
    saved_run = persist_completed_evaluation(
        db,
        current_user,
        dataset_name=dataset_name,
        target_column=target_column,
        feature_columns=feature_columns,
        split_ratio=split_ratio,
        results=algorithm_results,
    )

The endpoint must obtain current_user from the verified authentication dependency. Never accept a user_id from the request body or query string.

## Guest and authenticated behavior

- Authenticated evaluation: the service assigns the persisted run to current_user.user_id.
- Guest evaluation: the service stores the run with user_id=None. It is not returned by any authenticated user's GET /history.
- The service stores the dataset name, target column, selected feature columns, split ratio, algorithm metrics, confusion matrix, class labels, completion status, and timestamp.
- The generated run identifier is returned by the service so the evaluation response can expose it to the results/report flow.

## Existing history routes

- GET /history: returns only the authenticated user's runs, newest first, with pagination.
- GET /history/{run_id}: returns the run's saved configuration and metrics only to its owner.
- DELETE /history/{run_id}: deletes the run and its algorithm-result rows only for its owner.

## Completion boundary

The history service and routes are implemented independently of the evaluation engine. Issue #43 owns the POST /evaluations route and execution pipeline. Until that route calls persist_completed_evaluation(), the authenticated-save path is not end-to-end and issue #62 must remain open. This document is the integration contract for that endpoint.
