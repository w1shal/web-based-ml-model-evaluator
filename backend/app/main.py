from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import cors_origins, validate_production_config
from .db import engine
from .middleware import SecurityMiddleware
from .models import Base
from .routers import auth, history


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Refuse to start in HTTPS-enforced mode with a missing or weak signing key.
    validate_production_config()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Web Based ML Model Evaluator",
    lifespan=lifespan,
)

# SecurityMiddleware reads forwarded scheme only when TRUST_PROXY is enabled.
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(history.router)


@app.exception_handler(RequestValidationError)
async def validation_handler(
    request: Request,
    exc: RequestValidationError,
):
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
