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
    validate_production_config()      # MLE-SEC-004: no weak secrets in HTTPS/production mode
    Base.metadata.create_all(engine)  # create tables on startup
    yield


app = FastAPI(title="Web Based ML Model Evaluator", lifespan=lifespan)
app.add_middleware(SecurityMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=cors_origins(),
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(history.router)
# Other members add their routers here, e.g. datasets, evaluations, reports.


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    fields = [{"field": ".".join(str(x) for x in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=400, content={"error": {
        "code": "INVALID_REQUEST", "message": "Invalid or missing fields", "fields": fields}})
