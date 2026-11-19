"""Database engine and per-operation SQLAlchemy sessions.

Set DATABASE_URL, e.g. postgresql+psycopg://user:password@localhost:5432/worldcuisine.
SQLite is the developer/test fallback when DATABASE_URL is unset.
"""
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./worldcuisine.db")
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
