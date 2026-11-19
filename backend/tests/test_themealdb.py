import pytest

from app.services import themealdb


def test_normalize_full_themealdb_meal_uses_upstream_id_and_area(db_countries):
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


def test_normalize_ignores_unsupported_area(db_countries):
    assert themealdb.normalize_meal({"idMeal": "1", "strMeal": "Food", "strArea": "Atlantis"}) is None


@pytest.fixture
 def_placeholder():
    pass
