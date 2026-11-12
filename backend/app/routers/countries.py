from fastapi import APIRouter, Query

from app.db import db
from app.schemas.common import ErrorResponse, Page
from app.schemas.country import CountryOut
from app.schemas.dish import DishSummary
from app.services import dish_service
from app.services.lookups import require_country

router = APIRouter(prefix="/countries", tags=["Countries"])


def _out(country: dict) -> dict:
    count = sum(1 for d in db.dishes.values() if d["country_id"] == country["id"])
    return {**country, "dish_count": count}


@router.get("", response_model=list[CountryOut], summary="List countries")
def list_countries(q: str | None = Query(None, description="Filter by country or cuisine name")):
    items = sorted(db.countries.values(), key=lambda c: c["name"])
    if q:
        needle = q.lower()
        items = [c for c in items if needle in c["name"].lower() or needle in c["cuisine"].lower()]
    return [_out(c) for c in items]


@router.get("/{country_id}", response_model=CountryOut, responses={404: {"model": ErrorResponse}},
            summary="Get one country")
def get_country(country_id: str):
    return _out(require_country(country_id))


@router.get("/{country_id}/dishes", response_model=Page[DishSummary],
            responses={404: {"model": ErrorResponse}}, summary="Dishes of one country")
def country_dishes(country_id: str, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    require_country(country_id)
    return dish_service.list_dishes(country_id=country_id, limit=limit, offset=offset)
