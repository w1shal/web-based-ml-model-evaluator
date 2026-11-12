"""Numeric dataset validation and train-only preprocessing."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from .errors import EvaluationError

@dataclass
class PreparedData:
    X: pd.DataFrame
    y: np.ndarray
    classes: list
    numeric_cols: list[str]
    info: dict

def prepare_data(df: pd.DataFrame, target: str, features: list[str], strategy: str) -> PreparedData:
    if strategy not in ("median_imputation", "drop_rows"):
        raise EvaluationError("INVALID_STRATEGY", "Unsupported missing-value strategy", 400)
    if not features:
        raise EvaluationError("NO_FEATURES", "Select at least one feature column", 400)
    if len(set(features)) != len(features):
        raise EvaluationError("DUPLICATE_FEATURES", "Feature columns must be unique", 400)
    if target in features:
        raise EvaluationError("TARGET_IN_FEATURES", "Target cannot also be a feature", 400)
    missing = [column for column in [target, *features] if column not in df.columns]
    if missing:
        raise EvaluationError("UNKNOWN_COLUMN", f"Unknown column(s): {', '.join(missing)}", 400)
    data = df[[*features, target]].copy()
    rows_total = len(data)
    data = data[data[target].notna()]
    dropped = 0
    if strategy == "drop_rows":
        before = len(data)
        data = data.dropna(subset=features)
        dropped = before - len(data)
    if data.empty:
        raise EvaluationError("NO_USABLE_ROWS", "No usable rows remain after missing-value handling", 422)
    for column in features:
        if not pd.api.types.is_numeric_dtype(data[column]) and not pd.api.types.is_bool_dtype(data[column]):
            raise EvaluationError("UNSUPPORTED_FEATURE_TYPE", f"Feature '{column}' must be numeric in this sprint", 422)
        data[column] = pd.to_numeric(data[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
    if strategy == "drop_rows":
        data = data.dropna(subset=features)
    if data.empty:
        raise EvaluationError("NO_USABLE_ROWS", "No usable rows remain after missing-value handling", 422)
    y_values = data[target]
    if pd.api.types.is_float_dtype(y_values) and not np.all(np.equal(np.mod(y_values.to_numpy(dtype=float), 1), 0)):
        raise EvaluationError("TARGET_NOT_DISCRETE", "Classification target must contain discrete labels", 422)
    try:
        classes, y = np.unique(y_values.to_numpy(), return_inverse=True)
    except TypeError:
        raise EvaluationError("TARGET_MIXED_TYPES", "Target contains incomparable mixed types", 422) from None
    if len(classes) < 2:
        raise EvaluationError("TARGET_SINGLE_CLASS", "Target requires at least two classes", 422)
    if np.bincount(y).min() < 2:
        raise EvaluationError("CLASS_TOO_SMALL", "Every class needs at least two rows", 422)
    info = {"rows_total": rows_total, "rows_used": int(len(data)), "rows_dropped_missing_features": dropped,
            "missing_value_strategy": strategy}
    return PreparedData(data[features], y, [v.item() if hasattr(v, "item") else v for v in classes],
                        list(features), info)

def build_preprocessor(feature_cols: list[str], scale: bool) -> ColumnTransformer:
    steps = [("impute", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scale", StandardScaler()))
    return ColumnTransformer([("numeric", Pipeline(steps), feature_cols)], remainder="drop")
