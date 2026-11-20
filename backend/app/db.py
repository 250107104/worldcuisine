"""PostgreSQL configuration and request-scoped transactions."""
import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import DBAPIError, DataError, IntegrityError, InterfaceError, OperationalError, TimeoutError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, DatabaseUnavailableError, InvalidReferenceError, ValidationError


def database_url() -> URL:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("Set DATABASE_URL in the environment or backend/.env.")
    url = make_url(value)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    if url.drivername != "postgresql+psycopg":
        raise RuntimeError("DATABASE_URL must use PostgreSQL with the psycopg driver.")
    return url


@lru_cache
def get_engine():
    return create_engine(database_url(), pool_pre_ping=True, hide_parameters=True)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_session():
    try:
        with Session(get_engine()) as session, session.begin():
            yield session
    except IntegrityError as exc:
        code = getattr(exc.orig, "sqlstate", None)
        if code == "23505":
            raise ConflictError("A record with these values already exists") from exc
        if code == "23503":
            raise InvalidReferenceError("A related record is missing or still in use") from exc
        if code in {"23502", "23514"}:
            raise ValidationError("The data violates a database constraint") from exc
        raise
    except DataError as exc:
        raise ValidationError("A value cannot be stored in PostgreSQL") from exc
    except TimeoutError as exc:
        raise DatabaseUnavailableError("The database is busy. Retry the request.") from exc
    except DBAPIError as exc:
        code = getattr(exc.orig, "sqlstate", None) or ""
        if code in {"40001", "40P01"}:
            raise ConflictError("A concurrent write conflicted with this request. Retry the request.") from exc
        if (exc.connection_invalidated or code.startswith("08") or code in {"53300", "57P01", "57P02", "57P03"}
                or (not code and isinstance(exc, (OperationalError, InterfaceError)))):
            raise DatabaseUnavailableError("The database is temporarily unavailable. Retry the request.") from exc
        raise


# Close the transaction before sending the response so commit failures can return an error.
DBSession = Annotated[Session, Depends(get_session, scope="function")]
