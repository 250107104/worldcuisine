"""Watchlist / favorites / tried. Business rules live here, not in the routes.

Rules:
- No duplicates in any list (409).
- A dish you already tried cannot be added to the watchlist (409).
- Marking a dish as tried removes it from the watchlist and stamps its country in the passport.
- A tried dish that has a review cannot be un-tried until the review is deleted (409).
- move-to-favorites only works for dishes in the watchlist.
"""
from app.core.exceptions import ConflictError, NotFoundError
from app.db import db, utcnow
from app.services import activity_service, dish_service, passport_service
from app.services.lookups import find_review, normalize_country_id, require_dish, require_user
from app.services.pagination import paginate

LOG_TYPE = {"watchlist": "watchlist", "favorites": "favorite", "tried": "tried"}


def list_items(user_id: str, kind: str, country_id=None, category=None, sort="recent",
               limit: int = 20, offset: int = 0) -> dict:
    require_user(user_id)
    if country_id:
        country_id = normalize_country_id(country_id)
    items = []
    for dish_id, added_at in db.collections[user_id][kind].items():
        dish = db.dishes[dish_id]
        if country_id and dish["country_id"] != country_id:
            continue
        if category and dish["category"].lower() != category.lower():
            continue
        items.append({"dish": dish_service.to_summary(dish), "added_at": added_at})
    if sort == "name":
        items.sort(key=lambda i: i["dish"]["name"].lower())
    else:
        items.sort(key=lambda i: i["added_at"], reverse=True)
    return paginate(items, limit, offset)


def add(user_id: str, kind: str, dish_id: str) -> dict:
    require_user(user_id)
    dish = require_dish(dish_id)
    cols = db.collections[user_id]
    if dish_id in cols[kind]:
        raise ConflictError(f"'{dish['name']}' is already in your {kind}")
    if kind == "watchlist" and dish_id in cols["tried"]:
        raise ConflictError(f"You already tried '{dish['name']}', so it cannot go on your watchlist")
    if kind == "tried":
        mark_tried(user_id, dish_id)
    else:
        cols[kind][dish_id] = utcnow()
        activity_service.log(user_id, LOG_TYPE[kind], dish)
    return {"dish": dish_service.to_summary(dish), "added_at": cols[kind][dish_id]}


def mark_tried(user_id: str, dish_id: str, strict: bool = True) -> bool:
    """Shared by 'add to tried' and by writing a review. strict=False ignores an existing entry."""
    dish = require_dish(dish_id)
    cols = db.collections[user_id]
    if dish_id in cols["tried"]:
        if strict:
            raise ConflictError(f"'{dish['name']}' is already marked as tried")
        return False
    cols["watchlist"].pop(dish_id, None)
    cols["tried"][dish_id] = utcnow()
    db.explored_dishes[user_id].setdefault(dish_id, utcnow())
    passport_service.stamp(user_id, dish["country_id"], strict=False)
    activity_service.log(user_id, "tried", dish)
    return True


def remove(user_id: str, kind: str, dish_id: str) -> None:
    require_user(user_id)
    cols = db.collections[user_id]
    if dish_id not in cols[kind]:
        raise NotFoundError(f"Dish '{dish_id}' is not in your {kind}")
    if kind == "tried" and find_review(user_id, dish_id):
        raise ConflictError("This dish has a review. Delete the review before removing it from tried")
    del cols[kind][dish_id]


def move_to_favorites(user_id: str, dish_id: str) -> dict:
    require_user(user_id)
    dish = require_dish(dish_id)
    cols = db.collections[user_id]
    if dish_id not in cols["watchlist"]:
        raise NotFoundError(f"'{dish['name']}' is not in your watchlist")
    if dish_id in cols["favorites"]:
        raise ConflictError(f"'{dish['name']}' is already in your favorites")
    del cols["watchlist"][dish_id]
    cols["favorites"][dish_id] = utcnow()
    activity_service.log(user_id, "favorite", dish)
    return {"dish": dish_service.to_summary(dish), "added_at": cols["favorites"][dish_id]}
