"""Business-logic tests. They need only pytest (no FastAPI) and call the services directly."""
import pytest

from app.core.exceptions import ConflictError, InvalidReferenceError, NotFoundError
from app.db import db
from app.seed import load_seed
from app.services import (collection_service as cols, dish_service, passport_service,
                          recommendation_service, review_service, user_service, activity_service)

CARBONARA, PIZZA, TERIYAKI = "1001", "1002", "1003"   # seeded ids (Italy, Italy, Japan)


@pytest.fixture(autouse=True)
def fresh_db():
    db.reset()
    load_seed(db)
    yield


def new_user(name="tester"):
    return user_service.create_user({"username": name})["id"]


def test_duplicate_username_conflict():
    new_user("anna")
    with pytest.raises(ConflictError):
        new_user("ANNA")


def test_dish_validation_rules():
    base = {"name": "Test Dish", "country_id": "italy", "category": "Pasta", "tags": [], "image": None,
            "ingredients": [{"name": "x", "measure": ""}], "instructions": "Cook it well."}
    dish = dish_service.create_dish(base)
    with pytest.raises(ConflictError):
        dish_service.create_dish(base)
    with pytest.raises(InvalidReferenceError):
        dish_service.create_dish({**base, "name": "Other", "country_id": "atlantis"})
    assert dish["country_name"] == "Italy"


def test_watchlist_rules_and_move_to_favorites():
    u = new_user()
    cols.add(u, "watchlist", CARBONARA)
    with pytest.raises(ConflictError):
        cols.add(u, "watchlist", CARBONARA)             # duplicate
    with pytest.raises(NotFoundError):
        cols.add(u, "watchlist", "999999")              # unknown dish
    cols.move_to_favorites(u, CARBONARA)
    assert cols.list_items(u, "watchlist")["items"] == []
    assert cols.list_items(u, "favorites")["total"] == 1
    with pytest.raises(NotFoundError):
        cols.move_to_favorites(u, CARBONARA)            # no longer in watchlist


def test_tried_removes_from_watchlist_and_stamps_country():
    u = new_user()
    cols.add(u, "watchlist", TERIYAKI)
    cols.add(u, "tried", TERIYAKI)
    assert cols.list_items(u, "watchlist")["items"] == []
    passport = passport_service.get_passport(u)
    assert passport["explored"] == 1 and passport["rank"] == "Tourist"
    with pytest.raises(ConflictError):
        cols.add(u, "watchlist", TERIYAKI)              # already tried
    with pytest.raises(ConflictError):
        passport_service.unstamp(u, "japan")            # stamp earned by a tried dish


def test_review_workflow_consistency():
    u = new_user()
    cols.add(u, "watchlist", CARBONARA)
    review, created = review_service.upsert_review(u, CARBONARA, 5, "Creamy and perfect carbonara.")
    assert created
    assert cols.list_items(u, "tried")["items"][0]["dish"]["id"] == CARBONARA       # auto-tried
    assert cols.list_items(u, "watchlist")["items"] == []                           # left the watchlist
    assert passport_service.get_passport(u)["explored"] == 1               # stamped
    # edit keeps the same review id
    again, created = review_service.upsert_review(u, CARBONARA, 4, "Still great, a bit salty though.")
    assert not created and again["id"] == review["id"]
    # rating change syncs the review stars
    review_service.set_rating(u, CARBONARA, 2)
    assert review_service.get_review(u, CARBONARA)["rating"] == 2
    # review blocks removing rating / un-trying
    with pytest.raises(ConflictError):
        review_service.delete_rating(u, CARBONARA)
    with pytest.raises(ConflictError):
        cols.remove(u, "tried", CARBONARA)
    review_service.delete_review(u, CARBONARA)
    cols.remove(u, "tried", CARBONARA)
    assert dish_service.get_dish(CARBONARA)["average_rating"] == 2.0       # rating survived


def test_community_rating_average():
    a, b = new_user("a"), new_user("b")
    review_service.set_rating(a, PIZZA, 5)
    review_service.set_rating(b, PIZZA, 2)
    dish = dish_service.get_dish(PIZZA)
    assert dish["average_rating"] == 3.5 and dish["rating_count"] == 2


def test_delete_dish_conflict_and_force_cascade():
    u = new_user()
    review_service.upsert_review(u, PIZZA, 5, "Blistered crust, wonderful pizza.")
    with pytest.raises(ConflictError):
        dish_service.delete_dish(PIZZA)
    dish_service.delete_dish(PIZZA, force=True)
    assert review_service.list_user_reviews(u)["items"] == []
    assert cols.list_items(u, "tried")["items"] == []
    with pytest.raises(NotFoundError):
        dish_service.get_dish(PIZZA)


def test_delete_user_cascades():
    u = new_user()
    review_service.upsert_review(u, PIZZA, 4, "Really good margherita pizza.")
    user_service.delete_user(u)
    assert not [r for r in db.reviews.values() if r["user_id"] == u]
    with pytest.raises(NotFoundError):
        user_service.get_stats(u)


def test_recommendations_prefer_new_countries_and_liked_categories():
    u = new_user()
    review_service.upsert_review(u, CARBONARA, 5, "Creamy and perfect carbonara.")
    recs = recommendation_service.recommend(u, limit=50)
    ids = [r["dish"]["id"] for r in recs]
    assert CARBONARA not in ids                         # already tried
    assert recs[0]["dish"]["country_id"] != "italy"     # unexplored countries rank first
    with pytest.raises(NotFoundError):
        recommendation_service.recommend(u, country_id="atlantis")


def test_activity_feed_limit_and_filter():
    u = new_user()
    cols.add(u, "watchlist", CARBONARA)
    review_service.set_rating(u, PIZZA, 4)
    assert len(activity_service.list_activity(u)) == 2
    assert [a["type"] for a in activity_service.list_activity(u, type_="rating")] == ["rating"]
    assert len(activity_service.list_activity(u, limit=1)) == 1


def test_stats():
    u = new_user()
    review_service.upsert_review(u, CARBONARA, 5, "Creamy and perfect carbonara.")
    review_service.set_rating(u, PIZZA, 3)
    s = user_service.get_stats(u)
    assert s["tried"] == 1 and s["reviews"] == 1 and s["countries"] == 1
    assert s["rated_count"] == 2 and s["average_rating"] == 4.0


# ---------- country id normalisation ----------
def test_country_ids_are_case_insensitive():
    base = {"name": "Lasagne", "country_id": "Italy", "category": "Pasta", "tags": [], "image": None,
            "ingredients": [{"name": "x", "measure": ""}], "instructions": "Layer and bake it."}
    dish = dish_service.create_dish(base)
    assert dish["country_id"] == "italy"                                    # stored in canonical form
    assert dish_service.list_dishes(country_id="ITALY")["total"] == 3       # 2 seeded + new
    with pytest.raises(NotFoundError):
        dish_service.list_dishes(country_id="Atlantis")
    u = new_user()
    passport_service.stamp(u, "France")
    assert passport_service.get_passport(u)["explored"] == 1
    with pytest.raises(ConflictError):
        passport_service.stamp(u, " FRANCE ")                              # same stamp, other spelling
    passport_service.unstamp(u, "France")
    assert passport_service.get_passport(u)["explored"] == 0
    assert recommendation_service.recommend(u, country_id="Japan")          # no NotFoundError


# ---------- changing a dish's country ----------
def test_country_change_blocked_when_dish_was_tried():
    u = new_user()
    cols.add(u, "tried", TERIYAKI)                                          # stamps Japan
    with pytest.raises(ConflictError):
        dish_service.update_dish(TERIYAKI, {"country_id": "china"})
    assert dish_service.get_dish(TERIYAKI)["country_id"] == "japan"         # unchanged
    # same country (any case) is not a change; other fields stay editable
    assert dish_service.update_dish(TERIYAKI, {"country_id": "JAPAN", "category": "Grill"})["category"] == "Grill"
    # a dish nobody tried can move
    assert dish_service.update_dish(PIZZA, {"country_id": "Spain"})["country_id"] == "spain"
    with pytest.raises(InvalidReferenceError):
        dish_service.update_dish(PIZZA, {"country_id": "atlantis"})


# ---------- force delete cleans the activity feed ----------
def test_force_delete_removes_activity_entries():
    u = new_user()
    cols.add(u, "watchlist", PIZZA)
    cols.add(u, "watchlist", CARBONARA)
    dish_service.delete_dish(PIZZA, force=True)
    feed = activity_service.list_activity(u)
    assert [a["dish_id"] for a in feed] == [CARBONARA]


# ---------- pagination ----------
def test_list_endpoints_are_paginated():
    u = new_user()
    for dish_id in (CARBONARA, PIZZA, TERIYAKI):
        review_service.set_rating(u, dish_id, 4)
        cols.add(u, "watchlist", dish_id)
    page = cols.list_items(u, "watchlist", limit=2, offset=1)
    assert page["total"] == 3 and len(page["items"]) == 2 and page["offset"] == 1
    assert review_service.list_ratings(u, limit=2)["total"] == 3
    assert len(review_service.list_ratings(u, limit=2)["items"]) == 2
    for dish_id in (CARBONARA, PIZZA):
        review_service.upsert_review(u, dish_id, 5, "Wonderful, would order again.")
    assert review_service.list_user_reviews(u, limit=1)["total"] == 2
    new_user("second")
    assert user_service.list_users(limit=1)["total"] == 3                   # demo user + 2
