from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Country, Dish
from app.services.lookups import require_country


def _view(country: Country, count: int) -> dict:
    return {"id": country.id, "name": country.name, "iso2": country.iso2, "iso3": country.iso3,
            "cuisine": country.cuisine, "dish_count": count}


def list_countries(session: Session, q: str | None = None) -> list[dict]:
    stmt = select(Country, func.count(Dish.id)).outerjoin(Dish).group_by(Country.id)
    rows = sorted(session.execute(stmt), key=lambda row: row[0].name)
    if q:
        needle = q.lower()
        rows = [(c, count) for c, count in rows if needle in c.name.lower() or needle in c.cuisine.lower()]
    return [_view(country, count) for country, count in rows]


def get_country(session: Session, country_id: str) -> dict:
    country = require_country(session, country_id)
    count = session.scalar(select(func.count()).select_from(Dish).where(Dish.country_id == country.id))
    return _view(country, count)
