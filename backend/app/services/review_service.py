"""Reviews use the rating row as their single source of stars."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.db import utcnow
from app.models import Rating, Review
from app.services import activity_service, collection_service, dish_service
from app.services.lookups import find_review, require_dish, require_user
from app.services.pagination import paginate


def _view(review: Review) -> dict:
    return {"id": review.id, "user_id": review.user_id, "username": review.user.username,
            "dish_id": review.dish_id, "dish_name": review.dish.name, "rating": review.rating.stars,
            "text": review.text, "created_at": review.created_at.isoformat(),
            "updated_at": review.updated_at.isoformat()}


def _require_review(session: Session, user_id: str, dish_id: str) -> Review:
    require_user(session, user_id)
    require_dish(session, dish_id)
    review = find_review(session, user_id, dish_id)
    if review is None:
        raise NotFoundError("You have not reviewed this dish")
    return review


def upsert_review(session: Session, user_id: str, dish_id: str, rating: int, text: str) -> tuple[dict, bool]:
    user = require_user(session, user_id, lock=True)
    dish = require_dish(session, dish_id, lock=True)
    collection_service.mark_tried(session, user_id, dish)

    review = find_review(session, user_id, dish_id)
    stars = session.get(Rating, (user_id, dish_id))
    if stars is None:
        stars = Rating(user_id=user_id, dish_id=dish_id, stars=rating)
        session.add(stars)
    else:
        stars.stars = rating

    now = utcnow()
    created = review is None
    if created:
        review = Review(user=user, dish=dish, rating=stars, created_at=now)
        session.add(review)
    review.text = text
    review.updated_at = now
    activity_service.log(session, user_id, "review", dish, detail=rating)
    return _view(review), created


def get_review(session: Session, user_id: str, dish_id: str) -> dict:
    return _view(_require_review(session, user_id, dish_id))


def list_user_reviews(session: Session, user_id: str, min_rating: int | None = None, sort: str = "newest",
                      limit: int = 20, offset: int = 0) -> dict:
    require_user(session, user_id)
    stmt = select(Review).join(Review.rating).where(Review.user_id == user_id)
    if min_rating:
        stmt = stmt.where(Rating.stars >= min_rating)
    if sort == "rating":
        stmt = stmt.order_by(Rating.stars.desc(), Review.created_at, Review.id)
    else:
        stmt = stmt.order_by(Review.created_at.desc(), Review.id)
    return _review_page(session, stmt, limit, offset)


def list_dish_reviews(session: Session, dish_id: str, limit: int = 20, offset: int = 0) -> dict:
    require_dish(session, dish_id)
    stmt = select(Review).where(Review.dish_id == dish_id).order_by(Review.created_at.desc(), Review.id)
    return _review_page(session, stmt, limit, offset)


def _review_page(session: Session, stmt, limit: int, offset: int) -> dict:
    page = paginate(list(session.scalars(stmt)), limit, offset)
    page["items"] = [_view(review) for review in page["items"]]
    return page


def delete_review(session: Session, user_id: str, dish_id: str) -> None:
    require_user(session, user_id, lock=True)
    session.delete(_require_review(session, user_id, dish_id))


def set_rating(session: Session, user_id: str, dish_id: str, rating: int) -> dict:
    require_user(session, user_id, lock=True)
    dish = require_dish(session, dish_id, lock=True)
    entry = session.get(Rating, (user_id, dish_id))
    if entry is None or entry.stars != rating:
        if entry is None:
            session.add(Rating(user_id=user_id, dish_id=dish_id, stars=rating))
        else:
            entry.stars = rating
        review = find_review(session, user_id, dish_id)
        if review is not None:
            review.updated_at = utcnow()
        activity_service.log(session, user_id, "rating", dish, detail=rating)
    return {"dish": dish_service.to_summary(session, dish), "rating": rating}


def list_ratings(session: Session, user_id: str, limit: int = 20, offset: int = 0) -> dict:
    require_user(session, user_id)
    entries = list(session.scalars(
        select(Rating).where(Rating.user_id == user_id).order_by(Rating.created_at, Rating.dish_id)
    ))
    page = paginate(entries, limit, offset)
    summaries = dish_service.summaries(session, [entry.dish for entry in page["items"]])
    page["items"] = [{"dish": summaries[entry.dish_id], "rating": entry.stars} for entry in page["items"]]
    return page


def delete_rating(session: Session, user_id: str, dish_id: str) -> None:
    require_user(session, user_id, lock=True)
    require_dish(session, dish_id)
    entry = session.get(Rating, (user_id, dish_id))
    if entry is None:
        raise NotFoundError("You have not rated this dish")
    if find_review(session, user_id, dish_id):
        raise ConflictError("This dish has a review, so its rating cannot be removed. Delete the review first")
    session.delete(entry)
