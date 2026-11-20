from fastapi import APIRouter, Query

from app.db import DBSession
from app.schemas.common import ErrorResponse, Page
from app.schemas.input import InputText
from app.schemas.country import CountryOut
from app.schemas.dish import DishSummary
from app.services import country_service, dish_service

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.get("", response_model=list[CountryOut], summary="List countries")
def list_countries(session: DBSession, q: InputText | None = Query(None, description="Filter by country or cuisine name")):
    return country_service.list_countries(session, q)


@router.get("/{country_id}", response_model=CountryOut, responses={404: {"model": ErrorResponse}},
            summary="Get one country")
def get_country(session: DBSession, country_id: InputText):
    return country_service.get_country(session, country_id)


@router.get("/{country_id}/dishes", response_model=Page[DishSummary],
            responses={404: {"model": ErrorResponse}}, summary="Dishes of one country")
def country_dishes(session: DBSession, country_id: InputText,
                   limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return dish_service.list_dishes(session, country_id=country_id, limit=limit, offset=offset)
