"""Fetch a resource or raise the existing domain error."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Country, Dish, Review, User


def require_user(session: Session, user_id: str, *, lock: bool = False) -> User:
    user = session.get(User, user_id, with_for_update=lock or None)
    if user is None:
        raise NotFoundError(f"User '{user_id}' not found")
    return user


def require_dish(session: Session, dish_id: str, *, lock: bool = False) -> Dish:
    stmt = select(Dish).where(Dish.id == dish_id)
    if lock:
        stmt = stmt.with_for_update(of=Dish)
    dish = session.scalar(stmt)
    if dish is None:
        raise NotFoundError(f"Dish '{dish_id}' not found")
    return dish


def normalize_country_id(country_id: str) -> str:
    return country_id.strip().lower()


def require_country(session: Session, country_id: str) -> Country:
    country = session.get(Country, normalize_country_id(country_id))
    if country is None:
        raise NotFoundError(f"Country '{country_id}' not found")
    return country


def find_review(session: Session, user_id: str, dish_id: str) -> Review | None:
    return session.scalar(select(Review).where(Review.user_id == user_id, Review.dish_id == dish_id))
