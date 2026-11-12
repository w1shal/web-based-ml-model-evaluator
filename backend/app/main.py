from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import cors_origins, validate_production_config
from .db import engine
from .middleware import SecurityMiddleware
from .models import Base
from .routers import auth, history, reports, evaluations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Refuse HTTPS-enforced deployments with a missing or weak JWT secret.
    validate_production_config()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Web Based ML Model Evaluator",
    lifespan=lifespan,
)

# Trust forwarded scheme only when TRUST_PROXY is enabled.
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(history.router)
app.include_router(reports.router)
app.include_router(evaluations.router)
app.include_router(evaluations.algorithms_router)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    fields = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Invalid or missing fields",
                "fields": fields,
            }
        },
    )
