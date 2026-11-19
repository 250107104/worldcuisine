"""WorldCuisine REST API."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.database import SessionLocal, engine
from app.db import db
from app.models import Base, Country
from app.persistence import STATE_LOCK, load_state, save_state
from app.routers import admin, collections, countries, dishes, passport, reviews, users
from app.seed import load_seed

log = logging.getLogger("worldcuisine")
DESCRIPTION = """WorldCuisine API. TheMealDB provides the meal catalog. PostgreSQL (configured with DATABASE_URL)
persists users, collections, reviews, ratings, country metadata and cached catalog records."""


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with STATE_LOCK, SessionLocal() as session:
        if session.scalar(select(Country.id).limit(1)) is None:
            db.reset()
            load_seed(db)
            save_state(session)
            session.commit()
    yield


app = FastAPI(title="WorldCuisine API", version="2.0.0", description=DESCRIPTION, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def persistent_unit_of_work(request: Request, call_next):
    # Keep the existing Assignment 5 services intact while giving each HTTP request
    # an atomic SQL-backed unit of work. The lock avoids lost updates in shared state.
    with STATE_LOCK, SessionLocal() as session:
        load_state(session)
        try:
            response = await call_next(request)
            if response.status_code < 400:
                save_state(session)
                session.commit()
            else:
                session.rollback()
            return response
        except Exception:
            session.rollback()
            raise


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors = [{"field": ".".join(str(p) for p in e["loc"] if p != "body") or "body",
               "message": e["msg"].removeprefix("Value error, ")} for e in exc.errors()]
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
