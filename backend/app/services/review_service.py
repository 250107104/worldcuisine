"""Reviews and ratings.

Rules:
- One review per user per dish: writing again edits it.
- Writing a review marks the dish as tried (and so removes it from the watchlist, stamps the country).
- A review's stars and the user's rating for that dish are always the same number.
- A rating cannot be deleted while a review for the dish exists (delete the review first).
- Deleting a review keeps the rating.
"""
from app.core.exceptions import ConflictError, NotFoundError
from app.db import db, utcnow
from app.services import activity_service, collection_service, dish_service
from app.services.lookups import find_review, require_dish, require_user
from app.services.pagination import paginate


def _view(review: dict) -> dict:
    return {**review, "username": db.users[review["user_id"]]["username"],
            "dish_name": db.dishes[review["dish_id"]]["name"]}


def upsert_review(user_id: str, dish_id: str, rating: int, text: str) -> tuple[dict, bool]:
    require_user(user_id)
    dish = require_dish(dish_id)
    collection_service.mark_tried(user_id, dish_id, strict=False)

    now = utcnow()
    review = find_review(user_id, dish_id)
    created = review is None
    if created:
        rid = db.next_id("review")
        review = {"id": rid, "user_id": user_id, "dish_id": dish_id, "created_at": now}
        db.reviews[rid] = review
    review.update(rating=rating, text=text, updated_at=now)
    db.ratings[user_id][dish_id] = rating
    activity_service.log(user_id, "review", dish, detail=rating)
    return _view(review), created


def get_review(user_id: str, dish_id: str) -> dict:
    require_user(user_id)
    require_dish(dish_id)
    review = find_review(user_id, dish_id)
    if not review:
        raise NotFoundError("You have not reviewed this dish")
    return _view(review)


def list_user_reviews(user_id: str, min_rating: int | None = None, sort: str = "newest",
                      limit: int = 20, offset: int = 0) -> dict:
    require_user(user_id)
    items = [r for r in db.reviews.values() if r["user_id"] == user_id]
    if min_rating:
        items = [r for r in items if r["rating"] >= min_rating]
    if sort == "rating":
        items.sort(key=lambda r: (-r["rating"], r["created_at"]))
    else:
        items.sort(key=lambda r: r["created_at"], reverse=True)
    return paginate([_view(r) for r in items], limit, offset)


def list_dish_reviews(dish_id: str, limit: int = 20, offset: int = 0) -> dict:
    require_dish(dish_id)
    items = sorted((r for r in db.reviews.values() if r["dish_id"] == dish_id),
                   key=lambda r: r["created_at"], reverse=True)
    return paginate([_view(r) for r in items], limit, offset)


def delete_review(user_id: str, dish_id: str) -> None:
    require_user(user_id)
    require_dish(dish_id)
    review = find_review(user_id, dish_id)
    if not review:
        raise NotFoundError("You have not reviewed this dish")
    del db.reviews[review["id"]]


# ---------- ratings ----------

def set_rating(user_id: str, dish_id: str, rating: int) -> dict:
    require_user(user_id)
    dish = require_dish(dish_id)
    previous = db.ratings[user_id].get(dish_id)
    if previous != rating:
        db.ratings[user_id][dish_id] = rating
        review = find_review(user_id, dish_id)
        if review:                      # keep review stars and rating in sync
            review.update(rating=rating, updated_at=utcnow())
        activity_service.log(user_id, "rating", dish, detail=rating)
    return {"dish": dish_service.to_summary(dish), "rating": rating}


def list_ratings(user_id: str, limit: int = 20, offset: int = 0) -> dict:
    require_user(user_id)
    items = [{"dish": dish_service.to_summary(db.dishes[d]), "rating": r}
             for d, r in db.ratings[user_id].items()]
    return paginate(items, limit, offset)


def delete_rating(user_id: str, dish_id: str) -> None:
    require_user(user_id)
    require_dish(dish_id)
    if dish_id not in db.ratings[user_id]:
        raise NotFoundError("You have not rated this dish")
    if find_review(user_id, dish_id):
        raise ConflictError("This dish has a review, so its rating cannot be removed. Delete the review first")
    del db.ratings[user_id][dish_id]
