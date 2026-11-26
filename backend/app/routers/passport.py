from fastapi import APIRouter, Depends, Response, status

from app.db import DBSession
from app.dependencies import require_user_access
from app.schemas.common import ErrorResponse
from app.schemas.input import InputText
from app.schemas.passport import ExploredOut, PassportOut, StampCreate, StampOut
from app.services import passport_service

router = APIRouter(prefix="/users/{user_id}", tags=["Culinary Passport"],
                   dependencies=[Depends(require_user_access)])
ERR = {404: {"model": ErrorResponse}, 409: {"model": ErrorResponse},
       401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}}


@router.get("/passport", response_model=PassportOut, responses=ERR,
            summary="Your passport with progress, rank and country stamps")
def get_passport(session: DBSession, user_id: InputText):
    return passport_service.get_passport(session, user_id)


@router.post("/passport/stamps", response_model=StampOut, status_code=status.HTTP_201_CREATED, responses=ERR,
             summary="Stamp a country manually (409 if already stamped)",
             description="Stamps are also added automatically when you try or review a dish from a country.")
def add_stamp(session: DBSession, user_id: InputText, body: StampCreate):
    return passport_service.stamp(session, user_id, body.country_id)


@router.delete("/passport/stamps/{country_id}", status_code=status.HTTP_204_NO_CONTENT, responses=ERR,
               summary="Remove one of your stamps (409 if earned by a tried dish)")
def remove_stamp(session: DBSession, user_id: InputText, country_id: InputText):
    passport_service.unstamp(session, user_id, country_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/explored-dishes/{dish_id}", response_model=ExploredOut, responses=ERR,
             summary="Record that you opened a dish's recipe (idempotent)")
def mark_explored(session: DBSession, user_id: InputText, dish_id: InputText):
    return {"dish_id": dish_id, "newly_explored": passport_service.mark_dish_explored(session, user_id, dish_id)}
