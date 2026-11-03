
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Web-Based ML Model Evaluator",
    description="API for evaluating machine learning models.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
