"""Deterministic ranking for algorithm result comparison."""
COMPARED_METRICS = ("accuracy", "precision", "recall", "f1_score", "roc_auc")


def compare(results: list[dict], metric: str = "f1_score") -> dict:
    completed = [row for row in results if row.get("status") == "completed"]

    def sort_key(row):
        metric_value = row.get(metric)
        accuracy = row.get("accuracy")
        return (-(metric_value if metric_value is not None else 0.0),
                -(accuracy if accuracy is not None else 0.0), row["algorithm"])

    ranking = [
        {"rank": rank, "algorithm": row["algorithm"], "name": row.get("name"),
         metric: row.get(metric), "accuracy": row.get("accuracy")}
        for rank, row in enumerate(sorted(completed, key=sort_key), start=1)
    ]
    best_by_metric = {}
    for key in COMPARED_METRICS:
        scored = [row for row in completed if row.get(key) is not None]
        if scored:
            best_by_metric[key] = sorted(scored, key=lambda row: (-row[key], row["algorithm"]))[0]["algorithm"]
    return {"ranking_metric": metric, "ranking": ranking, "best_by_metric": best_by_metric}
