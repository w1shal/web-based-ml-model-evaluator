import logging
from contextlib import asynccontextmanager
from http import HTTPStatus
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from .config import cors_origins, validate_production_config
from .db import engine
from .middleware import SecurityMiddleware
from .models import Base
from .routers import auth, datasets, evaluations, history, reports


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
app.include_router(datasets.router)
app.include_router(history.router)
app.include_router(reports.router)
app.include_router(evaluations.router)
app.include_router(evaluations.algorithms_router)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = uuid4().hex
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        response = JSONResponse(status_code=500, content={"error": {
            "code": "INTERNAL_SERVER_ERROR", "message": "Internal server error", "request_id": request_id,
        }})
    response.headers["X-Request-ID"] = request_id
    logging.getLogger("app.requests").info("request_id=%s status=%s", request_id, response.status_code)
    return response


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, headers=exc.headers, content={
        "detail": exc.detail,
        "error": {"code": HTTPStatus(exc.status_code).name, "message": exc.detail,
                  "request_id": request.state.request_id},
    })


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
                "request_id": request.state.request_id,
                "message": "Invalid or missing fields",
                "fields": fields,
            }
        },
    )
