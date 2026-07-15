"""
Module: main

FastAPI calculator application.

Exposes:
- GET  /          -> the calculator web page (Jinja2 template + JavaScript)
- GET  /health    -> health check used by Docker and monitoring
- POST /add, /subtract, /multiply, /divide -> JSON REST endpoints

Request/response bodies are validated with Pydantic models, and every
operation and error is logged to both the console and logs/app.log.
"""

from contextlib import asynccontextmanager
import logging
import logging.handlers
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.operations import add, subtract, multiply, divide
from app.database_init import init_db


# ---------------------------------------------------------------------------
# Logging setup: log INFO+ to the console and to a rotating file so the
# application keeps a persistent record of operations and errors.
# ---------------------------------------------------------------------------
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            LOG_DIR / "app.log", maxBytes=1_000_000, backupCount=3
        ),
    ],
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create missing database tables before accepting application traffic."""

    init_db()
    yield


app = FastAPI(
    title="FastAPI Calculator with Secure Users",
    description="Calculator API extended with a secure SQLAlchemy user model.",
    lifespan=lifespan,
)

# Jinja2 renders HTML templates from the templates/ directory.
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Pydantic models: FastAPI uses these to validate incoming JSON and to
# document the shape of successful and error responses.
# ---------------------------------------------------------------------------
class OperationRequest(BaseModel):
    """JSON body for every arithmetic endpoint."""

    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")


class OperationResponse(BaseModel):
    """Successful response containing the computed result."""

    result: float = Field(..., description="The result of the operation")


class ErrorResponse(BaseModel):
    """Error response returned when an operation fails."""

    error: str = Field(..., description="Error message")


# ---------------------------------------------------------------------------
# Exception handlers: convert framework errors into the {"error": ...} JSON
# shape the frontend expects, and log every failure.
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error("HTTPException on %s: %s", request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    messages = "; ".join(f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors())
    logger.error("ValidationError on %s: %s", request.url.path, messages)
    return JSONResponse(status_code=400, content={"error": messages})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def read_root(request: Request):
    """Serve the calculator web page."""
    logger.info("Serving calculator homepage")
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
async def health():
    """Lightweight health check for Docker healthchecks and CI smoke tests."""
    return {"status": "ok"}


@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(operation: OperationRequest):
    """Add two numbers."""
    try:
        result = add(operation.a, operation.b)
        logger.info("Add: %s + %s = %s", operation.a, operation.b, result)
        return OperationResponse(result=result)
    except Exception as exc:
        logger.error("Add operation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest):
    """Subtract the second number from the first."""
    try:
        result = subtract(operation.a, operation.b)
        logger.info("Subtract: %s - %s = %s", operation.a, operation.b, result)
        return OperationResponse(result=result)
    except Exception as exc:
        logger.error("Subtract operation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest):
    """Multiply two numbers."""
    try:
        result = multiply(operation.a, operation.b)
        logger.info("Multiply: %s * %s = %s", operation.a, operation.b, result)
        return OperationResponse(result=result)
    except Exception as exc:
        logger.error("Multiply operation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest):
    """Divide the first number by the second."""
    try:
        result = divide(operation.a, operation.b)
        logger.info("Divide: %s / %s = %s", operation.a, operation.b, result)
        return OperationResponse(result=result)
    except ValueError as exc:
        # Division by zero: a client error, reported with a 400 status.
        logger.error("Divide operation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Divide operation internal error: %s", exc)
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
