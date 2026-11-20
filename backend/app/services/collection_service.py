"""Watchlist, favorites and tried workflows."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.db import utcnow
from app.models import CollectionEntry, Dish
from app.services import activity_service, dish_service, passport_service
from app.services.lookups import find_review, normalize_country_id, require_dish, require_user
from app.services.pagination import paginate

LOG_TYPE = {"watchlist": "watchlist", "favorites": "favorite", "tried": "tried"}


def _view(entry: CollectionEntry, summary: dict) -> dict:
    return {"dish": summary, "added_at": entry.added_at.isoformat()}


def list_items(session: Session, user_id: str, kind: str, country_id=None, category=None, sort="recent",
               limit: int = 20, offset: int = 0) -> dict:
    require_user(session, user_id)
    stmt = select(CollectionEntry).where(CollectionEntry.user_id == user_id, CollectionEntry.kind == kind)
    entries = list(session.scalars(stmt.order_by(CollectionEntry.added_at, CollectionEntry.dish_id)))
    if country_id:
        entries = [e for e in entries if e.dish.country_id == normalize_country_id(country_id)]
    if category:
        entries = [e for e in entries if e.dish.category.lower() == category.lower()]
    if sort == "name":
        entries.sort(key=lambda e: e.dish.name.lower())
    else:
        entries.sort(key=lambda e: e.added_at, reverse=True)
    page = paginate(entries, limit, offset)
    summaries = dish_service.summaries(session, [e.dish for e in page["items"]])
    page["items"] = [_view(e, summaries[e.dish_id]) for e in page["items"]]
    return page


def add(session: Session, user_id: str, kind: str, dish_id: str) -> dict:
    require_user(session, user_id, lock=True)
    dish = require_dish(session, dish_id, lock=True)
    if session.get(CollectionEntry, (user_id, kind, dish_id)):
        raise ConflictError(f"'{dish.name}' is already in your {kind}")
    if kind == "watchlist" and session.get(CollectionEntry, (user_id, "tried", dish_id)):
        raise ConflictError(f"You already tried '{dish.name}', so it cannot go on your watchlist")
    if kind == "tried":
        entry = mark_tried(session, user_id, dish)
    else:
        entry = CollectionEntry(user_id=user_id, kind=kind, dish_id=dish_id, added_at=utcnow())
        session.add(entry)
        activity_service.log(session, user_id, LOG_TYPE[kind], dish)
    return _view(entry, dish_service.to_summary(session, dish))


def mark_tried(session: Session, user_id: str, dish: Dish) -> CollectionEntry:
    """Called with both the user and dish locked by the collection or review workflow."""
    entry = session.get(CollectionEntry, (user_id, "tried", dish.id))
    if entry is not None:
        return entry
    watch = session.get(CollectionEntry, (user_id, "watchlist", dish.id))
    if watch is not None:
        session.delete(watch)
    entry = CollectionEntry(user_id=user_id, kind="tried", dish_id=dish.id, added_at=utcnow())
    session.add(entry)
    passport_service.record_explored_dish(session, user_id, dish.id)
    passport_service.record_stamp(session, user_id, dish.country_id)
    activity_service.log(session, user_id, "tried", dish)
    return entry


def remove(session: Session, user_id: str, kind: str, dish_id: str) -> None:
    require_user(session, user_id, lock=True)
    entry = session.get(CollectionEntry, (user_id, kind, dish_id))
    if entry is None:
        raise NotFoundError(f"Dish '{dish_id}' is not in your {kind}")
    if kind == "tried" and find_review(session, user_id, dish_id):
        raise ConflictError("This dish has a review. Delete the review before removing it from tried")
    session.delete(entry)


def move_to_favorites(session: Session, user_id: str, dish_id: str) -> dict:
    require_user(session, user_id, lock=True)
    dish = require_dish(session, dish_id, lock=True)
    watch = session.get(CollectionEntry, (user_id, "watchlist", dish_id))
    if watch is None:
        raise NotFoundError(f"'{dish.name}' is not in your watchlist")
    if session.get(CollectionEntry, (user_id, "favorites", dish_id)):
        raise ConflictError(f"'{dish.name}' is already in your favorites")
    session.delete(watch)
    favorite = CollectionEntry(user_id=user_id, kind="favorites", dish_id=dish_id, added_at=utcnow())
    session.add(favorite)
    activity_service.log(session, user_id, "favorite", dish)
    return _view(favorite, dish_service.to_summary(session, dish))
