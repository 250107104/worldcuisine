"""Business-logic tests that call the services directly with a PostgreSQL session."""
import pytest

from app.core.exceptions import ConflictError, InvalidReferenceError, NotFoundError
from sqlalchemy import select

from app.models import Review
from app.services import (collection_service as cols, dish_service, passport_service,
                          recommendation_service, review_service, user_service, activity_service)

CARBONARA, PIZZA, TERIYAKI = "1001", "1002", "1003"   # seeded ids (Italy, Italy, Japan)


def new_user(session, name="tester"):
    return user_service.create_user(session, {"username": name})["id"]


def test_duplicate_username_conflict(session):
    new_user(session, "anna")
    with pytest.raises(ConflictError):
        new_user(session, "ANNA")


def test_dish_validation_rules(session):
    base = {"name": "Test Dish", "country_id": "italy", "category": "Pasta", "tags": [], "image": None,
            "ingredients": [{"name": "x", "measure": ""}], "instructions": "Cook it well."}
    dish = dish_service.create_dish(session, base)
    with pytest.raises(ConflictError):
        dish_service.create_dish(session, base)
    with pytest.raises(InvalidReferenceError):
        dish_service.create_dish(session, {**base, "name": "Other", "country_id": "atlantis"})
    assert dish["country_name"] == "Italy"


def test_watchlist_rules_and_move_to_favorites(session):
    u = new_user(session)
    cols.add(session, u, "watchlist", CARBONARA)
    with pytest.raises(ConflictError):
        cols.add(session, u, "watchlist", CARBONARA)             # duplicate
    with pytest.raises(NotFoundError):
        cols.add(session, u, "watchlist", "999999")              # unknown dish
    cols.move_to_favorites(session, u, CARBONARA)
    assert cols.list_items(session, u, "watchlist")["items"] == []
    assert cols.list_items(session, u, "favorites")["total"] == 1
    with pytest.raises(NotFoundError):
        cols.move_to_favorites(session, u, CARBONARA)            # no longer in watchlist


def test_tried_removes_from_watchlist_and_stamps_country(session):
    u = new_user(session)
    cols.add(session, u, "watchlist", TERIYAKI)
    cols.add(session, u, "tried", TERIYAKI)
    assert cols.list_items(session, u, "watchlist")["items"] == []
    passport = passport_service.get_passport(session, u)
    assert passport["explored"] == 1 and passport["rank"] == "Tourist"
    with pytest.raises(ConflictError):
        cols.add(session, u, "watchlist", TERIYAKI)              # already tried
    with pytest.raises(ConflictError):
        passport_service.unstamp(session, u, "japan")            # stamp earned by a tried dish


def test_review_workflow_consistency(session):
    u = new_user(session)
    cols.add(session, u, "watchlist", CARBONARA)
    review, created = review_service.upsert_review(session, u, CARBONARA, 5, "Creamy and perfect carbonara.")
    assert created
    assert cols.list_items(session, u, "tried")["items"][0]["dish"]["id"] == CARBONARA       # auto-tried
    assert cols.list_items(session, u, "watchlist")["items"] == []                           # left the watchlist
    assert passport_service.get_passport(session, u)["explored"] == 1               # stamped
    # edit keeps the same review id
    again, created = review_service.upsert_review(session, u, CARBONARA, 4, "Still great, a bit salty though.")
    assert not created and again["id"] == review["id"]
    # rating change syncs the review stars
    review_service.set_rating(session, u, CARBONARA, 2)
    assert review_service.get_review(session, u, CARBONARA)["rating"] == 2
    # review blocks removing rating / un-trying
    with pytest.raises(ConflictError):
        review_service.delete_rating(session, u, CARBONARA)
    with pytest.raises(ConflictError):
        cols.remove(session, u, "tried", CARBONARA)
    review_service.delete_review(session, u, CARBONARA)
    cols.remove(session, u, "tried", CARBONARA)
    assert dish_service.get_dish(session, CARBONARA)["average_rating"] == 2.0       # rating survived


def test_community_rating_average(session):
    a, b = new_user(session, "a"), new_user(session, "b")
    review_service.set_rating(session, a, PIZZA, 5)
    review_service.set_rating(session, b, PIZZA, 2)
    dish = dish_service.get_dish(session, PIZZA)
    assert dish["average_rating"] == 3.5 and dish["rating_count"] == 2


def test_delete_dish_conflict_and_force_cascade(session):
    u = new_user(session)
    review_service.upsert_review(session, u, PIZZA, 5, "Blistered crust, wonderful pizza.")
    with pytest.raises(ConflictError):
        dish_service.delete_dish(session, PIZZA)
    dish_service.delete_dish(session, PIZZA, force=True)
    assert review_service.list_user_reviews(session, u)["items"] == []
    assert cols.list_items(session, u, "tried")["items"] == []
    with pytest.raises(NotFoundError):
        dish_service.get_dish(session, PIZZA)


def test_delete_user_cascades(session):
    u = new_user(session)
    review_service.upsert_review(session, u, PIZZA, 4, "Really good margherita pizza.")
    user_service.delete_user(session, u)
    assert session.scalar(select(Review).where(Review.user_id == u)) is None
    with pytest.raises(NotFoundError):
        user_service.get_stats(session, u)


def test_recommendations_prefer_new_countries_and_liked_categories(session):
    u = new_user(session)
    review_service.upsert_review(session, u, CARBONARA, 5, "Creamy and perfect carbonara.")
    recs = recommendation_service.recommend(session, u, limit=50)
    ids = [r["dish"]["id"] for r in recs]
    assert CARBONARA not in ids                         # already tried
    assert recs[0]["dish"]["country_id"] != "italy"     # unexplored countries rank first
    with pytest.raises(NotFoundError):
        recommendation_service.recommend(session, u, country_id="atlantis")


def test_activity_feed_limit_and_filter(session):
    u = new_user(session)
    cols.add(session, u, "watchlist", CARBONARA)
    review_service.set_rating(session, u, PIZZA, 4)
    assert len(activity_service.list_activity(session, u)) == 2
    assert [a["type"] for a in activity_service.list_activity(session, u, type_="rating")] == ["rating"]
    assert len(activity_service.list_activity(session, u, limit=1)) == 1


def test_stats(session):
    u = new_user(session)
    review_service.upsert_review(session, u, CARBONARA, 5, "Creamy and perfect carbonara.")
    review_service.set_rating(session, u, PIZZA, 3)
    s = user_service.get_stats(session, u)
    assert s["tried"] == 1 and s["reviews"] == 1 and s["countries"] == 1
    assert s["rated_count"] == 2 and s["average_rating"] == 4.0


# ---------- country id normalisation ----------
def test_country_ids_are_case_insensitive(session):
    base = {"name": "Lasagne", "country_id": "Italy", "category": "Pasta", "tags": [], "image": None,
            "ingredients": [{"name": "x", "measure": ""}], "instructions": "Layer and bake it."}
    dish = dish_service.create_dish(session, base)
    assert dish["country_id"] == "italy"                                    # stored in canonical form
    assert dish_service.list_dishes(session, country_id="ITALY")["total"] == 3       # 2 seeded + new
    with pytest.raises(NotFoundError):
        dish_service.list_dishes(session, country_id="Atlantis")
    u = new_user(session)
    passport_service.stamp(session, u, "France")
    assert passport_service.get_passport(session, u)["explored"] == 1
    with pytest.raises(ConflictError):
        passport_service.stamp(session, u, " FRANCE ")                              # same stamp, other spelling
    passport_service.unstamp(session, u, "France")
    assert passport_service.get_passport(session, u)["explored"] == 0
    assert recommendation_service.recommend(session, u, country_id="Japan")          # no NotFoundError


# ---------- changing a dish's country ----------
def test_country_change_blocked_when_dish_was_tried(session):
    u = new_user(session)
    cols.add(session, u, "tried", TERIYAKI)                                          # stamps Japan
    with pytest.raises(ConflictError):
        dish_service.update_dish(session, TERIYAKI, {"country_id": "china"})
    assert dish_service.get_dish(session, TERIYAKI)["country_id"] == "japan"         # unchanged
    # same country (any case) is not a change; other fields stay editable
    assert dish_service.update_dish(session, TERIYAKI, {"country_id": "JAPAN", "category": "Grill"})["category"] == "Grill"
    # a dish nobody tried can move
    assert dish_service.update_dish(session, PIZZA, {"country_id": "Spain"})["country_id"] == "spain"
    with pytest.raises(InvalidReferenceError):
        dish_service.update_dish(session, PIZZA, {"country_id": "atlantis"})


# ---------- force delete cleans the activity feed ----------
def test_force_delete_removes_activity_entries(session):
    u = new_user(session)
    cols.add(session, u, "watchlist", PIZZA)
    cols.add(session, u, "watchlist", CARBONARA)
    dish_service.delete_dish(session, PIZZA, force=True)
    feed = activity_service.list_activity(session, u)
    assert [a["dish_id"] for a in feed] == [CARBONARA]


# ---------- pagination ----------
def test_list_endpoints_are_paginated(session):
    u = new_user(session)
    for dish_id in (CARBONARA, PIZZA, TERIYAKI):
        review_service.set_rating(session, u, dish_id, 4)
        cols.add(session, u, "watchlist", dish_id)
    page = cols.list_items(session, u, "watchlist", limit=2, offset=1)
    assert page["total"] == 3 and len(page["items"]) == 2 and page["offset"] == 1
    assert review_service.list_ratings(session, u, limit=2)["total"] == 3
    assert len(review_service.list_ratings(session, u, limit=2)["items"]) == 2
    for dish_id in (CARBONARA, PIZZA):
        review_service.upsert_review(session, u, dish_id, 5, "Wonderful, would order again.")
    assert review_service.list_user_reviews(session, u, limit=1)["total"] == 2
    new_user(session, "second")
    assert user_service.list_users(session, limit=1)["total"] == 3                   # demo user + 2


def test_country_relationship_loads_multiple_dishes_in_both_directions(session):
    from app.models import Country

    italy = session.get(Country, "italy")
    assert {dish.id for dish in italy.dishes} == {CARBONARA, PIZZA}
    assert all(dish.country is italy for dish in italy.dishes)
