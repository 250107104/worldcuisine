import random

from app.core.exceptions import ConflictError, InvalidReferenceError, NotFoundError
from app.db import db, utcnow
from app.services.lookups import normalize_country_id, require_country, require_dish
from app.services.pagination import paginate


def _community_stats(dish_id: str) -> tuple[float | None, int]:
    values = [r[dish_id] for r in db.ratings.values() if dish_id in r]
    if not values:
        return None, 0
    return round(sum(values) / len(values), 1), len(values)


def to_summary(dish: dict) -> dict:
    average, count = _community_stats(dish["id"])
    return {
        "id": dish["id"], "name": dish["name"], "country_id": dish["country_id"],
        "country_name": db.countries[dish["country_id"]]["name"],
        "category": dish["category"], "image": dish["image"],
        "average_rating": average, "rating_count": count,
    }


def to_detail(dish: dict) -> dict:
    return {**to_summary(dish), "tags": dish["tags"], "ingredients": dish["ingredients"],
            "instructions": dish["instructions"], "created_at": dish["created_at"]}


def list_dishes(q=None, country_id=None, category=None, ingredient=None,
                sort="name", limit=20, offset=0) -> dict:
    if country_id:
        country_id = require_country(country_id)["id"]      # 'Italy' -> 'italy', unknown -> 404

    items = list(db.dishes.values())
    if q:
        items = [d for d in items if q.lower() in d["name"].lower()]
    if country_id:
        items = [d for d in items if d["country_id"] == country_id]
    if category:
        items = [d for d in items if d["category"].lower() == category.lower()]
    if ingredient:
        items = [d for d in items if any(ingredient.lower() in i["name"].lower() for i in d["ingredients"])]

    summaries = [to_summary(d) for d in items]
    if sort == "rating":
        # unrated dishes go last
        summaries.sort(key=lambda s: (s["average_rating"] is None, -(s["average_rating"] or 0), s["name"]))
    elif sort == "newest":
        created = {d["id"]: d["created_at"] for d in items}
        summaries.sort(key=lambda s: created[s["id"]], reverse=True)
    else:
        summaries.sort(key=lambda s: s["name"].lower())

    return paginate(summaries, limit, offset)


def list_categories() -> list[str]:
    return sorted({d["category"] for d in db.dishes.values()})


def get_dish(dish_id: str) -> dict:
    return to_detail(require_dish(dish_id))


def random_dish(country_id=None) -> dict:
    if country_id:
        country_id = require_country(country_id)["id"]
    pool = [d for d in db.dishes.values() if not country_id or d["country_id"] == country_id]
    if not pool:
        raise NotFoundError("No dishes available")
    return to_detail(random.choice(pool))


def _check_duplicate(name: str, country_id: str, ignore_id: str | None = None) -> None:
    for d in db.dishes.values():
        if d["id"] != ignore_id and d["country_id"] == country_id and d["name"].lower() == name.lower():
            raise ConflictError(f"'{name}' already exists in {db.countries[country_id]['name']} (dish id {d['id']})")


def create_dish(data: dict) -> dict:
    country_id = normalize_country_id(data["country_id"])
    if country_id not in db.countries:
        raise InvalidReferenceError(f"Country '{data['country_id']}' does not exist")
    _check_duplicate(data["name"], country_id)
    dish_id = db.next_id("dish")
    dish = {**data, "country_id": country_id, "id": dish_id, "created_at": utcnow()}
    db.dishes[dish_id] = dish
    return to_detail(dish)


def update_dish(dish_id: str, changes: dict) -> dict:
    dish = require_dish(dish_id)
    changes = dict(changes)
    if "country_id" in changes:
        new_country = normalize_country_id(changes["country_id"])
        if new_country not in db.countries:
            raise InvalidReferenceError(f"Country '{changes['country_id']}' does not exist")
        changes["country_id"] = new_country
        if new_country != dish["country_id"]:
            tried_by = sum(1 for c in db.collections.values() if dish_id in c["tried"])
            if tried_by:
                # passport stamps were earned through this dish's country, so moving it would make them wrong
                raise ConflictError(
                    f"{tried_by} user(s) already tried this dish, so its country cannot be changed "
                    "(their passport stamps depend on it)"
                )
    _check_duplicate(changes.get("name", dish["name"]), changes.get("country_id", dish["country_id"]), ignore_id=dish_id)
    dish.update(changes)
    return to_detail(dish)


def _references(dish_id: str) -> dict:
    return {
        "reviews": sum(1 for r in db.reviews.values() if r["dish_id"] == dish_id),
        "ratings": sum(1 for r in db.ratings.values() if dish_id in r),
        "saved_in_collections": sum(1 for c in db.collections.values() for kind in c.values() if dish_id in kind),
    }


def delete_dish(dish_id: str, force: bool = False) -> None:
    require_dish(dish_id)
    refs = _references(dish_id)
    if any(refs.values()) and not force:
        raise ConflictError(
            f"Dish is still used by users ({refs['reviews']} reviews, {refs['ratings']} ratings, "
            f"{refs['saved_in_collections']} saved entries). Retry with ?force=true to delete it everywhere."
        )
    for rid in [r for r, v in db.reviews.items() if v["dish_id"] == dish_id]:
        del db.reviews[rid]
    for table in (db.ratings, db.explored_dishes):
        for per_user in table.values():
            per_user.pop(dish_id, None)
    for per_user in db.collections.values():
        for kind in per_user.values():
            kind.pop(dish_id, None)
    for uid, entries in db.activity.items():             # no feed entries about a dish that no longer exists
        db.activity[uid] = [e for e in entries if e["dish_id"] != dish_id]
    del db.dishes[dish_id]
