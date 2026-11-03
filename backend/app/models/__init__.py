
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evaluation_runs = relationship(
        "EvaluationRun",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    dataset_name = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="evaluation_runs")
    algorithm_results = relationship(
        "AlgorithmResult",
        back_populates="evaluation_run",
        cascade="all, delete-orphan",
    )


class AlgorithmResult(Base):
    __tablename__ = "algorithm_results"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_run_id = Column(
        Integer,
        ForeignKey("evaluation_runs.id"),
        nullable=False,
    )
    algorithm_name = Column(String(100), nullable=False)
    metrics_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evaluation_run = relationship(
        "EvaluationRun",
        back_populates="algorithm_results",
    )