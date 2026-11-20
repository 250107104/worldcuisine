import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.import_catalog import CatalogError, import_catalog
from app.main import app
from app.models import Country, Dish

RECIPE = {
    "idMeal": "67901", "strMeal": "API Recipe",
    "strCountry": "Italy", "strArea": None, "strCategory": "Pasta",
    "strInstructions": "Make the pasta and serve it hot.",
    "strIngredient1": "pasta", "strMeasure1": "1 cup",
    "strMealThumb": "https://example.com/recipe.jpg", "strTags": "pasta",
}


def api_response(request):
    if request.url.path == "/list.php":
        return httpx.Response(200, json={"meals": [
            {"strCountry": "Italy", "strArea": "Italian"},
            {"strCountry": "Brazil", "strArea": "Brazilian"},
        ]})
    assert request.url.path == "/search.php"
    meals = [RECIPE, RECIPE | {"idMeal": "67902", "strMeal": "Brazilian Meal", "strCountry": None,
                               "strArea": "Brazilian"}] if request.url.params["f"] == "a" else None
    return httpx.Response(200, json={"meals": meals})


def test_import_from_api_and_keep_catalog_on_reset(test_engine):
    with httpx.Client(transport=httpx.MockTransport(api_response), base_url="https://example.com") as upstream:
        assert import_catalog(test_engine, upstream)["dishes_added"] == 2
        assert import_catalog(test_engine, upstream)["dishes_added"] == 0

    with TestClient(app) as client:
        country = client.get("/countries/brazil").json()
        assert country["name"] == "Brazil" and country["cuisine"] == "Brazilian" and country["dish_count"] == 1
        dish = client.get("/dishes/mealdb-67901").json()
        assert dish["name"] == RECIPE["strMeal"] and dish["country_id"] == "italy"
        assert dish["ingredients"] == [{"name": "pasta", "measure": "1 cup"}]
        assert client.put("/users/u1/reviews/mealdb-67901",
                          json={"rating": 5, "text": "I liked this imported recipe."}).status_code == 201
        assert client.post("/admin/reset").status_code == 200
        assert client.get("/dishes/mealdb-67901").status_code == 200
        assert client.get("/users/u1/reviews/mealdb-67901").status_code == 404


def test_upstream_error_does_not_partially_change_the_catalog(test_engine, session):
    def failing_response(request):
        if request.url.params.get("f") == "b":
            return httpx.Response(503)
        return api_response(request)

    with httpx.Client(transport=httpx.MockTransport(failing_response), base_url="https://example.com") as upstream:
        with pytest.raises(CatalogError):
            import_catalog(test_engine, upstream)
    assert session.get(Country, "brazil") is None
    assert session.scalar(select(Dish).where(Dish.id == "mealdb-67901")) is None


def test_fastapi_serves_the_website_and_its_public_assets():
    with TestClient(app) as client:
        assert client.get("/index.html").headers["content-type"].startswith("text/html")
        assert client.get("/profile.html").status_code == 200
        assert client.get("/js/storage.js").status_code == 200
        assert client.get("/backend/.env").status_code == 404
