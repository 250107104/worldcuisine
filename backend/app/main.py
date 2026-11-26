"""WorldCuisine REST API. Run:  uvicorn app.main:app --reload   then open http://127.0.0.1:8000/docs"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.routers import admin, auth, collections, countries, dishes, passport, reviews, users
from app.schemas.common import ErrorResponse, ValidationErrorResponse
from app.website import attach_website

log = logging.getLogger("worldcuisine")

DESCRIPTION = """
Backend for the **WorldCuisine** app: explore dishes by country, keep a watchlist, favorites and tried list,
write reviews, and collect passport stamps.

Data is stored in PostgreSQL. Alembic migrations create the schema and the demo user `u1`. Import the catalog with `python -m app.import_catalog`.

Errors have a `detail` message and a `code`. Invalid request fields also include an `errors` list.
"""


app = FastAPI(title="WorldCuisine API", version="1.0.0", description=DESCRIPTION)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        location = error["loc"]
        if location and location[0] == "body":
            location = location[1:]
        field = ".".join(str(part) for part in location) or "body"
        errors.append({"field": field, "message": error["msg"].removeprefix("Value error, ")})
    summary = "; ".join(f"{error['field']}: {error['message']}" for error in errors)
    return JSONResponse(status_code=422, content={"detail": summary, "code": "validation_error", "errors": errors})


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, exc: StarletteHTTPException):
    code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
    return JSONResponse(status_code=exc.status_code, headers=exc.headers,
                        content={"detail": str(exc.detail), "code": code})


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "code": "server_error"})


for module in (auth, countries, dishes, users, collections, reviews, passport, admin):
    app.include_router(module.router, responses={
        422: {"model": ValidationErrorResponse, "description": "Validation or invalid reference"},
        503: {"model": ErrorResponse, "description": "Database temporarily unavailable"},
    })


@app.get("/", tags=["Meta"], summary="API info")
def root():
    return {"name": "WorldCuisine API", "docs": "/docs", "version": app.version}


@app.get("/health", tags=["Meta"], summary="Health check")
def health():
    return {"status": "ok"}


attach_website(app)
