"""End-to-end HTTP tests. Run:  pytest   (needs fastapi, httpx, pytest)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

U = "/users/u1"           # demo user created by the seed
CARBONARA, PIZZA, TERIYAKI = "1001", "1002", "1003"


@pytest.fixture
def client():
    with TestClient(app) as c:        # entering the context runs the lifespan: fresh seeded data
        yield c


def error_code(response):
    assert response.json()["code"]
    return response.json()["code"]


# ---------- catalog ----------
def test_dish_search_filters_and_paging(client):
    r = client.get("/dishes", params={"country": "italy"})
    assert r.status_code == 200 and r.json()["total"] == 2
    assert client.get("/dishes", params={"q": "chicken"}).json()["total"] >= 4
    assert client.get("/dishes", params={"ingredient": "saffron"}).json()["total"] == 1
    page = client.get("/dishes", params={"limit": 5, "offset": 5}).json()
    assert len(page["items"]) == 5 and page["offset"] == 5


def test_dish_query_validation(client):
    assert client.get("/dishes", params={"limit": 0}).status_code == 422
    assert client.get("/dishes", params={"sort": "price"}).status_code == 422
    r = client.get("/dishes", params={"country": "atlantis"})
    assert r.status_code == 404 and error_code(r) == "not_found"


def test_dish_crud_and_rules(client):
    body = {"name": "Lasagne", "country_id": "italy", "category": "Pasta",
            "ingredients": [{"name": "pasta sheets", "measure": "12"}, {"name": "ragu", "measure": "500 g"}],
            "instructions": "Layer pasta, ragu and bechamel, then bake until bubbling."}
    r = client.post("/dishes", json=body)
    assert r.status_code == 201
    dish_id = r.json()["id"]
    assert client.post("/dishes", json=body).status_code == 409                       # duplicate
    assert client.post("/dishes", json={**body, "name": "X1", "country_id": "mars"}).status_code == 422
    bad = client.post("/dishes", json={**body, "name": "Dup ing", "ingredients": [{"name": "a"}, {"name": "A"}]})
    assert bad.status_code == 422 and error_code(bad) == "validation_error"
    assert client.post("/dishes", json={"name": "x"}).status_code == 422             # missing fields

    assert client.patch(f"/dishes/{dish_id}", json={"category": "Baked"}).json()["category"] == "Baked"
    assert client.patch(f"/dishes/{dish_id}", json={}).status_code == 422             # empty patch
    assert client.patch(f"/dishes/{dish_id}", json={"name": None}).status_code == 422
    assert client.patch("/dishes/999999", json={"category": "Baked"}).status_code == 404
    assert client.delete(f"/dishes/{dish_id}").status_code == 204
    assert client.get(f"/dishes/{dish_id}").status_code == 404


def test_random_and_categories_routes_not_shadowed(client):
    assert client.get("/dishes/random").status_code == 200
    assert "Dessert" in client.get("/dishes/categories").json()


# ---------- users ----------
def test_user_lifecycle(client):
    r = client.post("/users", json={"username": "Maria", "avatar": "🍕"})
    assert r.status_code == 201
    uid = r.json()["id"]
    assert client.post("/users", json={"username": "maria"}).status_code == 409
    assert client.post("/users", json={"username": " a "}).status_code == 422
    assert client.post("/users", json={"username": "Bob", "avatar": "x"}).status_code == 422
    assert client.patch(f"/users/{uid}", json={"bio": "Loves pasta"}).json()["bio"] == "Loves pasta"
    assert client.patch(f"/users/{uid}", json={"username": "Food Explorer"}).status_code == 409
    assert client.get(f"/users/{uid}/stats").json()["tried"] == 0
    assert client.delete(f"/users/{uid}").status_code == 204
    assert client.get(f"/users/{uid}").status_code == 404


# ---------- workflow 1: collections ----------
def test_collections_workflow(client):
    add = lambda kind, dish: client.post(f"{U}/collections/{kind}", json={"dish_id": dish})
    assert add("watchlist", CARBONARA).status_code == 201
    assert add("watchlist", CARBONARA).status_code == 409
    assert add("watchlist", "999999").status_code == 404
    assert client.post(f"{U}/collections/basket", json={"dish_id": PIZZA}).status_code == 422
    assert client.post(f"{U}/collections/watchlist", json={"dish_id": " "}).status_code == 422

    assert client.post(f"{U}/collections/watchlist/{CARBONARA}/move-to-favorites").status_code == 200
    assert client.get(f"{U}/collections/watchlist").json()["items"] == []
    assert client.get(f"{U}/collections/favorites").json()["total"] == 1
    assert client.post(f"{U}/collections/watchlist/{CARBONARA}/move-to-favorites").status_code == 404

    assert add("watchlist", TERIYAKI).status_code == 201
    assert add("tried", TERIYAKI).status_code == 201                       # leaves the watchlist
    assert client.get(f"{U}/collections/watchlist").json()["items"] == []
    assert add("watchlist", TERIYAKI).status_code == 409                   # already tried
    assert client.delete(f"{U}/collections/favorites/{CARBONARA}").status_code == 204
    assert client.delete(f"{U}/collections/favorites/{CARBONARA}").status_code == 404


# ---------- workflow 2: reviews & ratings ----------
def test_review_workflow(client):
    body = {"rating": 5, "text": "Creamy and perfect carbonara."}
    client.post(f"{U}/collections/watchlist", json={"dish_id": CARBONARA})
    r = client.put(f"{U}/reviews/{CARBONARA}", json=body)
    assert r.status_code == 201
    r2 = client.put(f"{U}/reviews/{CARBONARA}", json={"rating": 4, "text": "Still great, bit salty."})
    assert r2.status_code == 200 and r2.json()["id"] == r.json()["id"]

    assert client.get(f"{U}/collections/watchlist").json()["items"] == []            # auto-tried
    assert client.get(f"{U}/collections/tried").json()["total"] == 1
    assert client.get(f"{U}/passport").json()["explored"] == 1              # auto-stamped

    assert client.put(f"{U}/reviews/{CARBONARA}", json={"rating": 6, "text": "Too many stars here"}).status_code == 422
    assert client.put(f"{U}/reviews/{CARBONARA}", json={"rating": 3, "text": "short"}).status_code == 422
    assert client.put(f"{U}/reviews/999999", json=body).status_code == 404

    client.put(f"{U}/ratings/{CARBONARA}", json={"rating": 2})
    assert client.get(f"{U}/reviews/{CARBONARA}").json()["rating"] == 2     # synced
    assert client.delete(f"{U}/ratings/{CARBONARA}").status_code == 409
    assert client.delete(f"{U}/collections/tried/{CARBONARA}").status_code == 409

    assert client.get(f"/dishes/{CARBONARA}/reviews").json()["total"] == 1
    assert client.get(f"/dishes/{CARBONARA}").json()["average_rating"] == 2.0
    assert client.delete(f"/dishes/{CARBONARA}").status_code == 409         # still referenced
    assert client.delete(f"{U}/reviews/{CARBONARA}").status_code == 204
    assert client.delete(f"{U}/collections/tried/{CARBONARA}").status_code == 204
    assert client.delete(f"/dishes/{CARBONARA}", params={"force": True}).status_code == 204


# ---------- workflow 3: passport, activity, recommendations ----------
def test_passport_activity_recommendations(client):
    assert client.get(f"{U}/passport").json()["rank"] == "Newcomer"
    assert client.post(f"{U}/passport/stamps", json={"country_id": "france"}).status_code == 201
    assert client.post(f"{U}/passport/stamps", json={"country_id": "france"}).status_code == 409
    assert client.post(f"{U}/passport/stamps", json={"country_id": "narnia"}).status_code == 404
    client.post(f"{U}/collections/tried", json={"dish_id": TERIYAKI})
    assert client.delete(f"{U}/passport/stamps/japan").status_code == 409   # earned by a dish
    assert client.delete(f"{U}/passport/stamps/france").status_code == 204
    assert client.delete(f"{U}/passport/stamps/france").status_code == 404

    assert client.post(f"{U}/explored-dishes/{PIZZA}").json()["newly_explored"] is True
    assert client.post(f"{U}/explored-dishes/{PIZZA}").json()["newly_explored"] is False

    feed = client.get(f"{U}/activity", params={"type": "tried"}).json()
    assert [a["type"] for a in feed] == ["tried"]
    assert client.get(f"{U}/activity", params={"type": "nope"}).status_code == 422

    recs = client.get(f"{U}/recommendations", params={"limit": 3}).json()
    assert len(recs) == 3 and all(TERIYAKI != r["dish"]["id"] for r in recs)
    assert client.get(f"{U}/recommendations", params={"country": "atlantis"}).status_code == 404
    assert client.get("/users/zzz/recommendations").status_code == 404


def test_unknown_route_and_method_use_error_format(client):
    r = client.get("/nope")
    assert r.status_code == 404 and r.json()["code"] == "not_found"
    assert client.patch("/countries").status_code == 405


# ---------- country id case ----------
def test_country_ids_accept_any_case(client):
    assert client.get("/dishes", params={"country": "Italy"}).json()["total"] == 2
    assert client.get("/countries/ITALY").status_code == 200
    assert client.get("/countries/Italy/dishes").json()["total"] == 2
    body = {"name": "Lasagne", "country_id": "Italy", "category": "Pasta",
            "ingredients": [{"name": "ragu", "measure": "500 g"}],
            "instructions": "Layer pasta, ragu and bechamel, then bake."}
    r = client.post("/dishes", json=body)
    assert r.status_code == 201 and r.json()["country_id"] == "italy"
    assert client.post(f"{U}/passport/stamps", json={"country_id": "France"}).status_code == 201
    assert client.delete(f"{U}/passport/stamps/FRANCE").status_code == 204


# ---------- changing a dish's country ----------
def test_cannot_move_a_tried_dish_to_another_country(client):
    client.post(f"{U}/collections/tried", json={"dish_id": TERIYAKI})
    r = client.patch(f"/dishes/{TERIYAKI}", json={"country_id": "china"})
    assert r.status_code == 409 and error_code(r) == "conflict"
    assert client.get(f"/dishes/{TERIYAKI}").json()["country_id"] == "japan"
    assert client.patch(f"/dishes/{PIZZA}", json={"country_id": "spain"}).status_code == 200   # untried: allowed
    assert client.patch(f"/dishes/{PIZZA}", json={"country_id": "mars"}).status_code == 422


# ---------- enum query parameters ----------
def test_enum_query_parameters(client):
    assert client.get(f"{U}/activity", params={"type": "review"}).status_code == 200
    r = client.get(f"{U}/activity", params={"type": "nope"})
    assert r.status_code == 422 and error_code(r) == "validation_error"
    assert client.get(f"{U}/reviews", params={"sort": "rating"}).status_code == 200
    assert client.get(f"{U}/reviews", params={"sort": "alphabet"}).status_code == 422


# ---------- pagination on every list ----------
def test_all_list_endpoints_return_pages(client):
    for i in range(3):
        client.post("/users", json={"username": f"user{i}"})
    users = client.get("/users", params={"limit": 2}).json()
    assert users["total"] == 4 and len(users["items"]) == 2 and users["limit"] == 2
    assert client.get("/users", params={"limit": 0}).status_code == 422
    assert client.get("/users", params={"offset": -1}).status_code == 422

    for dish in (CARBONARA, PIZZA, TERIYAKI):
        client.post(f"{U}/collections/watchlist", json={"dish_id": dish})
        client.put(f"{U}/ratings/{dish}", json={"rating": 4})
    page = client.get(f"{U}/collections/watchlist", params={"limit": 2, "offset": 2}).json()
    assert page["total"] == 3 and len(page["items"]) == 1 and page["offset"] == 2
    assert client.get(f"{U}/collections/watchlist", params={"limit": 101}).status_code == 422

    ratings = client.get(f"{U}/ratings", params={"limit": 2}).json()
    assert ratings["total"] == 3 and len(ratings["items"]) == 2

    client.put(f"{U}/reviews/{CARBONARA}", json={"rating": 5, "text": "Creamy and perfect carbonara."})
    client.put(f"{U}/reviews/{PIZZA}", json={"rating": 4, "text": "Blistered crust, lovely pizza."})
    reviews = client.get(f"{U}/reviews", params={"limit": 1}).json()
    assert reviews["total"] == 2 and len(reviews["items"]) == 1
    assert client.get(f"{U}/reviews", params={"limit": 1, "offset": 1}).json()["items"][0]["dish_id"] == CARBONARA
