"""Culinary Passport and explored recipes."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import PASSPORT_RANKS
from app.core.exceptions import ConflictError, NotFoundError
from app.db import utcnow
from app.models import CollectionEntry, Country, Dish, ExploredDish, PassportStamp
from app.services.lookups import require_country, require_dish, require_user


def _stamp_view(country: Country, stamp: PassportStamp | None) -> dict:
    return {"country_id": country.id, "name": country.name, "iso2": country.iso2,
            "explored_at": stamp.stamped_at.isoformat() if stamp else None}


def record_stamp(session: Session, user_id: str, country_id: str) -> PassportStamp | None:
    """Add a stamp under the caller's user lock. Return None if already stamped."""
    if session.get(PassportStamp, (user_id, country_id)) is not None:
        return None
    entry = PassportStamp(user_id=user_id, country_id=country_id, stamped_at=utcnow())
    session.add(entry)
    return entry


def stamp(session: Session, user_id: str, country_id: str) -> dict:
    require_user(session, user_id, lock=True)
    country = require_country(session, country_id)
    entry = record_stamp(session, user_id, country.id)
    if entry is None:
        raise ConflictError(f"Passport already stamped for '{country.id}'")
    return _stamp_view(country, entry)


def unstamp(session: Session, user_id: str, country_id: str) -> None:
    require_user(session, user_id, lock=True)
    country = require_country(session, country_id)
    entry = session.get(PassportStamp, (user_id, country.id))
    if entry is None:
        raise NotFoundError(f"No stamp for '{country.id}' in this passport")
    earned = session.scalar(select(func.count()).select_from(CollectionEntry).join(Dish).where(
        CollectionEntry.user_id == user_id, CollectionEntry.kind == "tried", Dish.country_id == country.id
    ))
    if earned:
        raise ConflictError(f"Stamp was earned by trying {earned} dish(es) from this country; unmark them as tried first")
    session.delete(entry)


def record_explored_dish(session: Session, user_id: str, dish_id: str) -> bool:
    if session.get(ExploredDish, (user_id, dish_id)) is not None:
        return False
    session.add(ExploredDish(user_id=user_id, dish_id=dish_id))
    return True


def mark_dish_explored(session: Session, user_id: str, dish_id: str) -> bool:
    require_user(session, user_id, lock=True)
    require_dish(session, dish_id, lock=True)
    return record_explored_dish(session, user_id, dish_id)


def get_passport(session: Session, user_id: str) -> dict:
    require_user(session, user_id)
    rows = list(session.execute(select(Country, PassportStamp).outerjoin(
        PassportStamp, (PassportStamp.country_id == Country.id) & (PassportStamp.user_id == user_id)
    )))
    rows.sort(key=lambda row: row[0].name)
    explored = sum(stamp is not None for _, stamp in rows)
    total = len(rows)
    return {"explored": explored, "total": total,
            "percent": round(explored / total * 100) if total else 0,
            "rank": next(title for minimum, title in PASSPORT_RANKS if explored >= minimum),
            "stamps": [_stamp_view(country, stamp) for country, stamp in rows]}
