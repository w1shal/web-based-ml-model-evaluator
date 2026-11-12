"""Request model for the evaluation endpoint."""
from pydantic import BaseModel, Field

class EvaluationRequest(BaseModel):
    dataset_id: str = Field(min_length=1, max_length=64)
    target_column: str = Field(min_length=1, max_length=255)
    feature_columns: list[str] = Field(min_length=1, max_length=500)
    algorithms: list[str] = Field(min_length=1, max_length=5)
    test_size: float = Field(default=0.2, ge=0.05, le=0.5)
    missing_value_strategy: str = Field(default="median_imputation", max_length=40)
