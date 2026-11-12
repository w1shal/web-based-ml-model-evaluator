"""Dataset validation and preprocessing for classification evaluation."""
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from .errors import EvaluationError

MISSING_STRATEGIES = ("median_imputation", "drop_rows")
MAX_CLASSES = 50


@dataclass
class PreparedData:
    X: pd.DataFrame
    y: np.ndarray
    classes: list
    numeric_cols: list
    categorical_cols: list
    info: dict


def _py(value: Any):
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def prepare_data(df: pd.DataFrame, target: str, features: list[str], strategy: str) -> PreparedData:
    if strategy not in MISSING_STRATEGIES:
        raise EvaluationError("INVALID_STRATEGY", f"Unsupported missing-value strategy. Use one of: {', '.join(MISSING_STRATEGIES)}", 400)
    if not features:
        raise EvaluationError("NO_FEATURES", "Select at least one feature column", 400)
    if len(set(features)) != len(features):
        raise EvaluationError("DUPLICATE_FEATURES", "Feature columns must be unique", 400)
    if target in features:
        raise EvaluationError("TARGET_IN_FEATURES", "The target column cannot also be a feature", 400)
    missing = [column for column in [target, *features] if column not in df.columns]
    if missing:
        raise EvaluationError("UNKNOWN_COLUMN", f"Unknown column(s): {', '.join(map(str, missing))}", 400)

    data = df[[*features, target]].copy()
    rows_total = len(data)
    for column in features:
        if pd.api.types.is_numeric_dtype(data[column]) and not pd.api.types.is_bool_dtype(data[column]):
            data[column] = data[column].astype(float).replace([np.inf, -np.inf], np.nan)

    missing_cells = {column: int(data[column].isna().sum()) for column in features if data[column].isna().any()}
    dropped_target = int(data[target].isna().sum())
    data = data[data[target].notna()]

    dropped_features = 0
    if strategy == "drop_rows":
        before = len(data)
        data = data.dropna(subset=features)
        dropped_features = before - len(data)
    if len(data) == 0:
        raise EvaluationError("NO_USABLE_ROWS", "No usable rows remain after handling missing values", 422)

    empty = [column for column in features if data[column].isna().all()]
    kept = [column for column in features if column not in empty]
    if not kept:
        raise EvaluationError("NO_USABLE_FEATURES", "All selected feature columns are empty", 422)

    numeric_cols, categorical_cols = [], []
    for column in kept:
        if pd.api.types.is_numeric_dtype(data[column]) or pd.api.types.is_bool_dtype(data[column]):
            data[column] = data[column].astype(float)
            numeric_cols.append(column)
        else:
            categorical_cols.append(column)
    if categorical_cols:
        raise EvaluationError("UNSUPPORTED_FEATURE_TYPE",
                              f"Non-numeric feature column(s) are not supported yet: {', '.join(categorical_cols)}", 422)

    raw = data[target]
    if pd.api.types.is_float_dtype(raw) and not np.all(np.equal(np.mod(raw.to_numpy(dtype=float), 1), 0)):
        raise EvaluationError("TARGET_NOT_DISCRETE", "The target column has continuous values; classification needs discrete labels", 422)
    try:
        encoder = LabelEncoder()
        y = encoder.fit_transform(raw.to_numpy())
    except TypeError:
        raise EvaluationError("TARGET_MIXED_TYPES", "The target column mixes different value types", 422)
    n_classes = len(encoder.classes_)
    if n_classes < 2:
        raise EvaluationError("TARGET_SINGLE_CLASS", "The target column needs at least two different classes", 422)
    if n_classes > MAX_CLASSES:
        raise EvaluationError("TARGET_TOO_MANY_CLASSES", f"The target has {n_classes} distinct values (maximum {MAX_CLASSES}); it looks continuous", 422)
    if np.bincount(y).min() < 2:
        raise EvaluationError("CLASS_TOO_SMALL", "Every class needs at least 2 rows", 422)

    info = {
        "missing_value_strategy": strategy,
        "rows_total": rows_total,
        "rows_used": int(len(data)),
        "rows_dropped_missing_target": dropped_target,
        "rows_dropped_missing_features": dropped_features,
        "missing_cells_by_column": missing_cells,
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "empty_features_removed": empty,
    }
    return PreparedData(X=data[kept], y=y, classes=[_py(value) for value in encoder.classes_],
                        numeric_cols=numeric_cols, categorical_cols=categorical_cols, info=info)


def build_preprocessor(numeric_cols: list, scale: bool) -> ColumnTransformer:
    """Fit imputers/scalers on the training split only."""
    steps = [("impute", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scale", StandardScaler()))
    return ColumnTransformer([("num", Pipeline(steps), numeric_cols)], remainder="drop")
