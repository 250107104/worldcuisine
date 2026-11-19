"""WorldCuisine REST API."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.database import SessionLocal, engine
from app.models import Base, Country
from app.seed import COUNTRIES
from app.routers import admin, collections, countries, dishes, passport, reviews, users

log = logging.getLogger("worldcuisine")
DESCRIPTION = """WorldCuisine API. PostgreSQL, configured through DATABASE_URL,
stores users, catalog cache, collections, ratings, reviews and passport data."""


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Alembic owns the schema. This only seeds reference countries for a new database.
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        if session.scalar(select(Country.id).limit(1)) is None:
            for cid, iso2, iso3, name, cuisine in COUNTRIES:
                session.add(Country(id=cid, iso2=iso2, iso3=iso3, name=name, cuisine=cuisine))
            session.commit()
    yield


app = FastAPI(title="WorldCuisine API", version="2.0.0", description=DESCRIPTION, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
async def handle_app_error(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request, exc):
    errors = [{"field": ".".join(str(p) for p in e["loc"] if p != "body") or "body",
               "message": e["msg"].removeprefix("Value error, ")} for e in exc.errors()] 
    summary = "; ".join(f"{e['field']}: {e['message']}" for e in errors)
    return JSONResponse(status_code=422, content={"detail": summary, "code": "validation_error", "errors": errors})


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request, exc):
    code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail), "code": code})


@app.exception_handler(Exception)
async def handle_unexpected(request, exc):
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
