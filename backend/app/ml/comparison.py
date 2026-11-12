"""Deterministic algorithm ranking for run result comparison."""
COMPARED_METRICS = ("accuracy", "precision", "recall", "f1_score", "roc_auc")


def compare(results: list[dict], metric: str = "f1_score") -> dict:
    done = [result for result in results if result.get("status") == "completed"]

    def sort_key(result):
        return (-(result.get(metric) or 0.0), -(result.get("accuracy") or 0.0), result["algorithm"])

    ranking = [
        {"rank": index, "algorithm": result["algorithm"], "name": result.get("name"),
         metric: result.get(metric), "accuracy": result.get("accuracy")}
        for index, result in enumerate(sorted(done, key=sort_key), start=1)
    ]
    best = {}
    for key in COMPARED_METRICS:
        scored = [result for result in done if result.get(key) is not None]
        if scored:
            best[key] = sorted(scored, key=lambda result: (-result[key], result["algorithm"]))[0]["algorithm"]
    return {"ranking_metric": metric, "ranking": ranking, "best_by_metric": best}
