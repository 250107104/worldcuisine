from fastapi import APIRouter, Query, Response, status

from app.db import DBSession
from app.dependencies import require_user_access
from app.schemas.common import ErrorResponse, Page
from app.schemas.input import InputText
from app.schemas.passport import ActivityOut, ActivityType, RecommendationOut
from app.schemas.user import UserCreate, UserOut, UserStats, UserUpdate
from app.services import activity_service, recommendation_service, user_service

router = APIRouter(prefix="/users", tags=["Users"])
NOT_FOUND = {404: {"model": ErrorResponse}}
AUTH_REQUIRED = {401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}}


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED,
             responses={409: {"model": ErrorResponse}}, summary="Create a user profile")
def create_user(session: DBSession, body: UserCreate):
    data = body.model_dump()
    if body.password is not None:
        data["password"] = body.password
    return user_service.create_user(session, data)


@router.get("", response_model=Page[UserOut], summary="List users")
def list_users(session: DBSession, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return user_service.list_users(session, limit, offset)


@router.get("/{user_id}", response_model=UserOut, responses={**NOT_FOUND, **AUTH_REQUIRED},
            dependencies=[Depends(require_user_access)], summary="Get your profile")
def get_user(session: DBSession, user_id: InputText):
    return user_service.get_user(session, user_id)


@router.patch("/{user_id}", response_model=UserOut,
              responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, **AUTH_REQUIRED},
              dependencies=[Depends(require_user_access)], summary="Edit your profile (partial)")
def update_user(session: DBSession, user_id: InputText, body: UserUpdate):
    changes = body.model_dump(exclude_unset=True)
    if "password" in body.model_fields_set:
        changes["password"] = body.password
    return user_service.update_user(session, user_id, changes)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT,
               responses={**NOT_FOUND, **AUTH_REQUIRED}, dependencies=[Depends(require_user_access)],
               summary="Delete your account and its data")
def delete_user(session: DBSession, user_id: InputText):
    user_service.delete_user(session, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{user_id}/stats", response_model=UserStats, responses={**NOT_FOUND, **AUTH_REQUIRED},
            dependencies=[Depends(require_user_access)], summary="Counts shown on your profile")
def stats(session: DBSession, user_id: InputText):
    return user_service.get_stats(session, user_id)


@router.get("/{user_id}/activity", response_model=list[ActivityOut],
            responses={**NOT_FOUND, **AUTH_REQUIRED}, dependencies=[Depends(require_user_access)],
            summary="Your activity feed (newest first, max 50 kept)")
def activity(session: DBSession, user_id: InputText,
             type: ActivityType | None = Query(None, description="Only this kind of event"),
             limit: int = Query(15, ge=1, le=50)):
    return activity_service.list_activity(session, user_id, type.value if type else None, limit)


@router.get("/{user_id}/recommendations", response_model=list[RecommendationOut],
            responses={**NOT_FOUND, **AUTH_REQUIRED}, dependencies=[Depends(require_user_access)],
            summary="Dishes you might like next")
def recommendations(session: DBSession, user_id: InputText,
                    limit: int = Query(5, ge=1, le=20),
                    country: InputText | None = Query(None, description="Only this country id"),
                    category: InputText | None = Query(None)):
    return recommendation_service.recommend(session, user_id, limit, country, category)
