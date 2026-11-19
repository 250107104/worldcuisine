"""Focused tests for TheMealDB normalization and filter endpoint shapes."""
import pytest

from app.db import db
from app.seed import load_seed
from app.services import themealdb


@pytest.fixture
def countries():
    db.reset()
    load_seed(db)
    yield
    db.reset()


def test_normalize_full_themealdb_meal_uses_upstream_id_and_area(countries):
    raw = {"idMeal": "52772", "strMeal": "  Teriyaki  ", "strArea": "Japanese",
           "strCategory": "Chicken", "strMealThumb": "https://example.test/meal.jpg",
           "strInstructions": "Cook it.", "strTags": "Dinner,Quick", "strIngredient1": "Chicken",
           "strMeasure1": "500 g", "strIngredient2": "", "strMeasure2": ""}
    meal = themealdb.normalize_meal(raw)
    assert meal["id"] == "52772"
    assert meal["name"] == "Teriyaki"
    assert meal["country_id"] == "japan"
    assert meal["ingredients"] == [{"name": "Chicken", "measure": "500 g"}]
    assert meal["tags"] == ["Dinner", "Quick"]


def test_normalize_short_area_filter_record_with_known_area(countries):
    raw = {"idMeal": "52772", "strMeal": "Teriyaki", "strMealThumb": "https://example.test/meal.jpg"}
    meal = themealdb.normalize_meal(raw, area="Japanese")
    assert meal["country_id"] == "japan"
    assert meal["instructions"] is None


def test_normalize_ignores_unsupported_area(countries):
    assert themealdb.normalize_meal({"idMeal": "1", "strMeal": "Food", "strArea": "Atlantis"}) is None


def test_filter_endpoint_ids_are_extracted(monkeypatch):
    monkeypatch.setattr(themealdb, "_get_json", lambda path, **params: {
        "meals": [{"idMeal": "52772", "strMeal": "Teriyaki", "strMealThumb": "image"}]
    })
    assert themealdb.get_filtered_ids("c", "Chicken") == {"52772"}
