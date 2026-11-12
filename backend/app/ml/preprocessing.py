"""Numeric and categorical dataset validation with train-only preprocessing."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .errors import EvaluationError

MAX_CATEGORIES_PER_FEATURE = 50


@dataclass
class PreparedData:
    X: pd.DataFrame
    y: np.ndarray
    classes: list
    numeric_cols: list[str]
    categorical_cols: list[str]
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
    data = data[data[target].notna()].copy()
    if data.empty:
        raise EvaluationError("NO_USABLE_ROWS", "No usable rows remain after missing-value handling", 422)

    numeric_cols, categorical_cols = [], []
    for column in features:
        if pd.api.types.is_numeric_dtype(data[column]) or pd.api.types.is_bool_dtype(data[column]):
            numeric_cols.append(column)
            data[column] = pd.to_numeric(data[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
        else:
            categorical_cols.append(column)
            # Normalize category values to strings so mixed object columns are encoder-safe.
            data[column] = data[column].map(lambda value: str(value) if pd.notna(value) else np.nan)
            category_count = data[column].nunique(dropna=True)
            if category_count > MAX_CATEGORIES_PER_FEATURE:
                raise EvaluationError(
                    "TOO_MANY_CATEGORIES",
                    f"Feature '{column}' has more than {MAX_CATEGORIES_PER_FEATURE} distinct categories",
                    422,
                )

    rows_dropped = 0
    if strategy == "drop_rows":
        before = len(data)
        data = data.dropna(subset=features)
        rows_dropped = before - len(data)
    if data.empty:
        raise EvaluationError("NO_USABLE_ROWS", "No usable rows remain after missing-value handling", 422)

    y_values = data[target]
    if pd.api.types.is_float_dtype(y_values) and not np.all(
        np.equal(np.mod(y_values.to_numpy(dtype=float), 1), 0)
    ):
        raise EvaluationError("TARGET_NOT_DISCRETE", "Classification target must contain discrete labels", 422)
    try:
        classes, y = np.unique(y_values.to_numpy(), return_inverse=True)
    except TypeError:
        raise EvaluationError("TARGET_MIXED_TYPES", "Target contains incomparable mixed types", 422) from None
    if len(classes) < 2:
        raise EvaluationError("TARGET_SINGLE_CLASS", "Target requires at least two classes", 422)
    if np.bincount(y).min() < 2:
        raise EvaluationError("CLASS_TOO_SMALL", "Every class needs at least two rows", 422)

    info = {
        "rows_total": rows_total,
        "rows_used": int(len(data)),
        "rows_dropped_missing_features": int(rows_dropped),
        "missing_value_strategy": strategy,
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
    }
    labels = [value.item() if hasattr(value, "item") else value for value in classes]
    return PreparedData(data[features], y, labels, numeric_cols, categorical_cols, info)


def build_preprocessor(numeric_cols: list[str], categorical_cols: list[str], scale: bool) -> ColumnTransformer:
    transformers = []
    if numeric_cols:
        numeric_steps = [("impute", SimpleImputer(strategy="median", keep_empty_features=True))]
        if scale:
            numeric_steps.append(("scale", StandardScaler()))
        transformers.append(("numeric", Pipeline(numeric_steps), numeric_cols))
    if categorical_cols:
        categorical_steps = [
            ("impute", SimpleImputer(strategy="most_frequent", keep_empty_features=True)),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
        transformers.append(("categorical", Pipeline(categorical_steps), categorical_cols))
    return ColumnTransformer(transformers, remainder="drop")
