"""WorldCuisine REST API. Run:  uvicorn app.main:app --reload   then open http://127.0.0.1:8000/docs"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.db import db
from app.routers import admin, collections, countries, dishes, passport, reviews, users
from app.seed import load_seed

log = logging.getLogger("worldcuisine")

DESCRIPTION = """
Backend for the **WorldCuisine** app: explore dishes by country, keep a watchlist, favorites and tried list,
write reviews, and collect passport stamps.

Data lives in memory and is reset to a small seed each time the server starts
(or by `POST /admin/reset`). A demo user `u1` exists from the start.

**Errors** always look like `{"detail": "...", "code": "not_found | conflict | invalid_reference | validation_error"}`.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.reset()
    load_seed(db)
    yield


app = FastAPI(title="WorldCuisine API", version="1.0.0", description=DESCRIPTION, lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(p) for p in e["loc"] if p != "body") or "body",
         "message": e["msg"].removeprefix("Value error, ")}
        for e in exc.errors()
    ]
    summary = "; ".join(f"{e['field']}: {e['message']}" for e in errors)
    return JSONResponse(status_code=422, content={"detail": summary, "code": "validation_error", "errors": errors})


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, exc: StarletteHTTPException):
    code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail), "code": code})


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "code": "server_error"})


for module in (countries, dishes, users, collections, reviews, passport, admin):
    app.include_router(module.router)


@app.get("/", tags=["Meta"], summary="API info")
def root():
    return {"name": "WorldCuisine API", "docs": "/docs", "version": app.version}


@app.get("/health", tags=["Meta"], summary="Health check")
def health():
    return {"status": "ok"}
