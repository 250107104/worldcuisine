"""Run the existing workflows against a disposable PostgreSQL database."""
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Country, Dish, User


@pytest.fixture(scope="session")
def test_engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database")
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("DATABASE_URL", url)
        get_engine.cache_clear()
        command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
        engine = get_engine()
        try:
            yield engine
        finally:
            engine.dispose()
            get_engine.cache_clear()


@pytest.fixture(autouse=True)
def fresh_db(test_engine):
    with Session(test_engine) as session, session.begin():
        session.execute(text(
            "TRUNCATE activity, passport_stamps, explored_dishes, reviews, ratings, "
            "collection_entries, dishes, users, countries RESTART IDENTITY"
        ))
        # Test records are inserted only into the disposable pytest database.
        session.add_all([
            Country(id="italy", iso2="it", iso3="ITA", name="Italy", cuisine="Italian"),
            Country(id="japan", iso2="jp", iso3="JPN", name="Japan", cuisine="Japanese"),
            Country(id="france", iso2="fr", iso3="FRA", name="France", cuisine="French"),
            Country(id="china", iso2="cn", iso3="CHN", name="China", cuisine="Chinese"),
            Country(id="spain", iso2="es", iso3="ESP", name="Spain", cuisine="Spanish"),
            User(id="u1", username="Food Explorer", avatar="🍜", bio=""),
        ])
        session.flush()
        dishes = [
            ("italy", "Test Pasta", "Pasta", "pasta"),
            ("italy", "Test Pizza", "Pasta", "flour"),
            ("japan", "Test Teriyaki", "Chicken", "rice"),
            ("france", "Test Dessert", "Dessert", "sugar"),
            ("spain", "Test Saffron Rice", "Seafood", "saffron"),
            ("china", "Test Vegetables", "Side", "carrots"),
        ]
        dishes.extend(("china", f"Test Chicken {index}", "Chicken", "rice") for index in range(4))
        session.add_all([
            Dish(id=str(dish_id), country_id=country, name=name, category=category,
                 instructions="Test recipe instructions.", tags=[],
                 ingredients=[{"name": ingredient, "measure": "1 cup"}])
            for dish_id, (country, name, category, ingredient) in enumerate(dishes, start=1001)
        ])


@pytest.fixture
def session(test_engine):
    with Session(test_engine) as db_session, db_session.begin():
        yield db_session
