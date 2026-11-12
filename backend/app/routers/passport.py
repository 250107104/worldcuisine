from fastapi import APIRouter, Response, status

from app.schemas.common import ErrorResponse
from app.schemas.passport import ExploredOut, PassportOut, StampCreate, StampOut
from app.services import passport_service

router = APIRouter(prefix="/users/{user_id}", tags=["Culinary Passport"])
ERR = {404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}}


@router.get("/passport", response_model=PassportOut, responses={404: {"model": ErrorResponse}},
            summary="Passport with progress, rank and all country stamps")
def get_passport(user_id: str):
    return passport_service.get_passport(user_id)


@router.post("/passport/stamps", response_model=StampOut, status_code=status.HTTP_201_CREATED, responses=ERR,
             summary="Stamp a country manually (409 if already stamped)",
             description="Stamps are also added automatically when you try or review a dish from a country.")
def add_stamp(user_id: str, body: StampCreate):
    passport_service.stamp(user_id, body.country_id)
    return next(s for s in passport_service.get_passport(user_id)["stamps"] if s["country_id"] == body.country_id)


@router.delete("/passport/stamps/{country_id}", status_code=status.HTTP_204_NO_CONTENT, responses=ERR,
               summary="Remove a stamp (409 if earned by a tried dish)")
def remove_stamp(user_id: str, country_id: str):
    passport_service.unstamp(user_id, country_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/explored-dishes/{dish_id}", response_model=ExploredOut, responses={404: {"model": ErrorResponse}},
             summary="Record that the user opened a dish's recipe (idempotent)")
def mark_explored(user_id: str, dish_id: str):
    return {"dish_id": dish_id, "newly_explored": passport_service.mark_dish_explored(user_id, dish_id)}
