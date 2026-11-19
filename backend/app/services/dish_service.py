"""Catalog queries backed by TheMealDB; user ratings remain in the local store."""
import random

from app.core.exceptions import NotFoundError
from app.db import db
from app.services import themealdb
from app.services.lookups import normalize_country_id, require_country, require_dish
from app.services.pagination import paginate


def _community_stats(dish_id: str) -> tuple[float | None, int]:
    values = [ratings[dish_id] for ratings in db.ratings.values() if dish_id in ratings]
    return (round(sum(values) / len(values), 1), len(values)) if values else (None, 0)


def to_summary(dish: dict) -> dict:
    average, count = _community_stats(dish["id"])
    country = db.countries[dish["country_id"]]
    return {"id": dish["id"], "name": dish["name"], "country_id": dish["country_id"],
            "country_name": country["name"], "category": dish.get("category"), "image": dish.get("image"),
            "average_rating": average, "rating_count": count}


def to_detail(dish: dict) -> dict:
    if dish.get("category") is None or dish.get("instructions") is None:
        dish = require_dish(dish["id"])
    return {**to_summary(dish), "tags": dish.get("tags", []), "ingredients": dish.get("ingredients", []),
            "instructions": dish.get("instructions"), "created_at": dish.get("created_at")}


def _candidates(q=None, country_id=None, category=None, ingredient=None) -> list[dict]:
    if country_id:
        country_id = require_country(country_id)["id"]
    if q:
        items = themealdb.search(q)
    elif country_id:
        items = themealdb.get_by_area(db.countries[country_id]["cuisine"])
    else:
        items = themealdb.all_catalog_summaries()

    if country_id:
        items = [dish for dish in items if dish["country_id"] == country_id]
    if category:
        matches = {d["id"] for d in themealdb.get_by_category(category)}
        items = [dish for dish in items if dish["id"] in matches]
    if ingredient:
        matches = {d["id"] for d in themealdb.get_by_ingredient(ingredient)}
        items = [dish for dish in items if dish["id"] in matches]
    for dish in items:
        db.dishes.setdefault(dish["id"], dish)
    return items


def list_dishes(q=None, country_id=None, category=None, ingredient=None,
                sort="name", limit=20, offset=0) -> dict:
    items = _candidates(q, country_id, category, ingredient)
    if sort == "rating":
        items.sort(key=lambda d: (_community_stats(d["id"])[0] is None,
                                  -(_community_stats(d["id"])[0] or 0), d["name"].casefold()))
    elif sort == "name":
        items.sort(key=lambda d: d["name"].casefold())
    # TheMealDB provides no creation timestamp; for "newest", retain upstream order.
    page = items[offset:offset + limit]
    summaries = [to_summary(require_dish(d["id"])) for d in page]
    return {"items": summaries, "total": len(items), "limit": limit, "offset": offset}


def list_categories() -> list[str]:
    return themealdb.get_categories()


def get_dish(dish_id: str) -> dict:
    return to_detail(require_dish(dish_id))


def random_dish(country_id=None) -> dict:
    if country_id:
        country = require_country(country_id)
        candidates = themealdb.get_by_area(country["cuisine"])
        if not candidates:
            raise NotFoundError("No dishes available for this country")
        return to_detail(random.choice(candidates))
    for _ in range(5):
        dish = themealdb.get_random()
        if dish:
            db.dishes[dish["id"]] = dish
            return to_detail(dish)
    raise NotFoundError("No dishes available")
