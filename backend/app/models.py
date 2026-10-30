
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


def utcnow() -> datetime:
    """Return a naive UTC timestamp."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(10), default="user", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )


class EvaluationRun(Base):
    """Stores an evaluation run and its owner."""

    __tablename__ = "evaluation_runs"

    run_id: Mapped[str] = mapped_column(
        String(40), primary_key=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.user_id"), nullable=True, index=True
    )
    dataset_name: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, index=True
    )
    target_column: Mapped[str] = mapped_column(String(255))
    feature_columns: Mapped[list] = mapped_column(JSON)
    split_ratio: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(
        String(20), default="completed"
    )

    results: Mapped[list[AlgorithmResult]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AlgorithmResult.result_id",
    )


class AlgorithmResult(Base):
    __tablename__ = "algorithm_results"

    result_id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
        index=True,
    )
    algorithm_name: Mapped[str] = mapped_column(String(50))
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roc_auc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confusion_matrix: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )
    serialized_metrics: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )

    run: Mapped[EvaluationRun] = relationship(back_populates="results")
