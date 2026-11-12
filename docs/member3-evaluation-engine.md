# Member 3 evaluation-engine implementation notes

## API contract
- `GET /algorithms` lists registered built-in and extension algorithms.
- `POST /evaluations` runs the requested one-to-five selected algorithms.
- `GET /evaluations/{run_id}` retrieves a saved run. Authenticated runs are owner-only; guest runs can be fetched by their generated run ID.
- Logged-in runs are persisted through the existing `save_run` history service. Guest runs have a null owner and do not appear in authenticated history.

## Algorithm and metric contract
- The five built-ins are Logistic Regression, Decision Tree, Random Forest, SVM and KNN.
- Two-class targets use binary averaging, treating the second sorted encoded class as positive.
- Multiclass targets use support-weighted precision, recall and F1.
- Confusion-matrix rows represent true labels; columns represent predicted labels.
- ROC-AUC is calculated for binary classification using estimator probabilities or decision scores. Multiclass ROC-AUC is explicitly not applicable.
- SVM uses its decision function, avoiding the extra cost of probability calibration.

## Preprocessing
- Numeric columns use median imputation; scale-sensitive models also standardize them.
- Categorical columns use most-frequent imputation and one-hot encoding.
- Unseen categories are ignored at transform time.
- Categorical features with more than 50 distinct values are rejected.
- Missing targets are removed and the train/test split is stratified with a fixed random seed.

## Dataset upload hand-off
The upload route should call `store_dataset(content, name, owner_id)` with validated CSV bytes, the original filename and the current user ID (or null for a guest). The evaluation service loads the CSV by dataset ID and checks ownership. A dataset owned by another account returns 404 to avoid ID probing.

## Concurrency and operations
- The concurrency gate is process-local. `EVAL_MAX_CONCURRENT` controls simultaneous evaluations and `EVAL_QUEUE_TIMEOUT` controls queue wait duration.
- Requests that exceed the queue timeout receive HTTP 503 with `Retry-After: 5`.
- Each Uvicorn worker has its own gate; this implementation does not provide a cluster-wide limit.
- Normal CI excludes timing-sensitive performance tests. Run them on the demo machine with `cd backend && python -m pytest -q -m performance --durations=10`.
- SQLite is covered by automated tests. PostgreSQL deployment, the production upload path, browser integration and multiple worker processes require separate validation.
