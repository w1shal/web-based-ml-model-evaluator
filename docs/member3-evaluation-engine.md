# Member 3 evaluation-engine implementation notes

This document records the design choices and integration contract for the Sprint 1 and Sprint 2 evaluation-engine work.

## API contract

- `GET /algorithms` lists the registered built-in and extension algorithms.
- `POST /evaluations` is synchronous and returns HTTP 200 with the run result after evaluation completes.
- A request must select between one and five algorithms. Duplicate IDs are collapsed while preserving request order; unknown IDs are rejected.
- `GET /evaluations/{run_id}` retrieves a saved result. Authenticated runs are owner-only; a guest run can be retrieved using its generated run ID.
- Logged-in runs are stored through Member 1's `save_run` service and appear in the authenticated user's `/history`. Guest runs are persisted with a null owner and are not listed in authenticated history.

## Metric definitions

- Accuracy, precision, recall and F1 are returned for each successfully trained algorithm.
- Two-class targets use binary averaging, with the second label in sorted label order treated as the positive class.
- Three-or-more-class targets use support-weighted precision, recall and F1. Tests include an imbalanced three-class dataset so weighted and macro averaging cannot accidentally appear equivalent.
- Confusion-matrix rows are true labels and columns are predicted labels. The result includes the original class labels in sorted encoding order.
- ROC-AUC is computed for binary classification. Multiclass runs explicitly mark ROC-AUC as not applicable.
- SVM uses its decision-function scores for binary ROC-AUC; probability calibration is not enabled. This avoids the additional fitting overhead of `probability=True`.

## Preprocessing choices

- Numeric features use median imputation; scale-sensitive algorithms also standardize numeric values.
- Categorical features use most-frequent imputation and one-hot encoding. Categories not present in the training partition are ignored at prediction time.
- A categorical feature with more than 50 distinct values is rejected with a controlled 422 response.
- Missing target labels are removed. The train/test split is stratified and uses a fixed random seed.

## Dataset upload hand-off

The repository does not yet contain the upload endpoint in this integration. Member 2's validated upload path should call:

```python
dataset_id = store_dataset(
    content=validated_csv_bytes,
    name=original_filename,
    owner_id=current_user.user_id if current_user else None,
)
```

The upload endpoint should return the generated `dataset_id`. The evaluation route loads the stored CSV using that ID and checks its owner. The API deliberately returns 404 for a dataset owned by another account so IDs cannot be probed.

## Concurrency and deployment

- The concurrency gate is per application process. `EVAL_MAX_CONCURRENT` controls simultaneous evaluations; `EVAL_QUEUE_TIMEOUT` controls how long queued requests wait.
- Requests that cannot obtain a slot before the timeout receive HTTP 503 with `Retry-After: 5`.
- Multiple Uvicorn worker processes each have their own gate. This implementation does not provide a cluster-wide concurrency limit.
- The automated CI workflow excludes tests marked `performance` because wall-clock thresholds are machine-dependent. Run the benchmark on the demo machine with:

```powershell
cd backend
python -m pytest -q -m performance --durations=10
```

- SQLite is covered by the tests. PostgreSQL, an end-to-end 10 MB upload route, browser integration, and multiple worker processes require separate deployment validation.
