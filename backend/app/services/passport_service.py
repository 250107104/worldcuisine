"""Culinary Passport: one stamp per country the user has explored."""
from app.core.constants import PASSPORT_RANKS
from app.core.exceptions import ConflictError, NotFoundError
from app.db import db, utcnow
from app.services.lookups import require_country, require_dish, require_user


def _rank(count: int) -> str:
    return next(title for minimum, title in PASSPORT_RANKS if count >= minimum)


def stamp(user_id: str, country_id: str, strict: bool = True) -> bool:
    """Adds a stamp. Returns True if new. strict=False silently ignores a repeat (used by auto-stamping)."""
    require_user(user_id)
    country_id = require_country(country_id)["id"]
    if country_id in db.stamps[user_id]:
        if strict:
            raise ConflictError(f"Passport already stamped for '{country_id}'")
        return False
    db.stamps[user_id][country_id] = utcnow()
    return True


def unstamp(user_id: str, country_id: str) -> None:
    require_user(user_id)
    country_id = require_country(country_id)["id"]
    if country_id not in db.stamps[user_id]:
        raise NotFoundError(f"No stamp for '{country_id}' in this passport")
    earned = [d for d in db.collections[user_id]["tried"] if db.dishes[d]["country_id"] == country_id]
    if earned:
        raise ConflictError(
            f"Stamp was earned by trying {len(earned)} dish(es) from this country; unmark them as tried first"
        )
    del db.stamps[user_id][country_id]


def mark_dish_explored(user_id: str, dish_id: str) -> bool:
    require_user(user_id)
    require_dish(dish_id)
    if dish_id in db.explored_dishes[user_id]:
        return False
    db.explored_dishes[user_id][dish_id] = utcnow()
    return True


def get_passport(user_id: str) -> dict:
    require_user(user_id)
    stamps = db.stamps[user_id]
    total = len(db.countries)
    entries = [
        {"country_id": c["id"], "name": c["name"], "iso2": c["iso2"], "explored_at": stamps.get(c["id"])}
        for c in sorted(db.countries.values(), key=lambda c: c["name"])
    ]
    return {
        "explored": len(stamps), "total": total,
        "percent": round(len(stamps) / total * 100) if total else 0,
        "rank": _rank(len(stamps)),
        "stamps": entries,
    }
