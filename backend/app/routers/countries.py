from fastapi import APIRouter, Query

from app.db import db
from app.schemas.common import ErrorResponse, Page
from app.schemas.country import CountryOut
from app.schemas.dish import DishSummary
from app.services import dish_service, themealdb
from app.services.lookups import require_country

router = APIRouter(prefix="/countries", tags=["Countries"])


def _out(country: dict, counts: dict[str, int]) -> dict:
    return {**country, "dish_count": counts.get(country["id"], 0)}


@router.get("", response_model=list[CountryOut], summary="List supported TheMealDB cuisine areas")
def list_countries(q: str | None = Query(None, description="Filter by country or cuisine name")):
    items = sorted(db.countries.values(), key=lambda c: c["name"])
    if q:
        needle = q.casefold()
        items = [c for c in items if needle in c["name"].casefold() or needle in c["cuisine"].casefold()]
    counts = themealdb.area_counts()
    return [_out(country, counts) for country in items]


@router.get("/{country_id}", response_model=CountryOut, responses={404: {"model": ErrorResponse}}, summary="Get one country")
def get_country(country_id: str):
    country = require_country(country_id)
    return _out(country, themealdb.area_counts())


@router.get("/{country_id}/dishes", response_model=Page[DishSummary],
            responses={404: {"model": ErrorResponse}}, summary="Dishes for a cuisine area")
def country_dishes(country_id: str, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    require_country(country_id)
    return dish_service.list_dishes(country_id=country_id, limit=limit, offset=offset)
