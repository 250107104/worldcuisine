from fastapi import APIRouter, Query, Response, status

from app.schemas.common import ErrorResponse, Page
from app.schemas.passport import ActivityOut, ActivityType, RecommendationOut
from app.schemas.user import UserCreate, UserOut, UserStats, UserUpdate
from app.services import activity_service, recommendation_service, user_service

router = APIRouter(prefix="/users", tags=["Users"])
NOT_FOUND = {404: {"model": ErrorResponse}}


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED,
             responses={409: {"model": ErrorResponse}}, summary="Create a user profile")
def create_user(body: UserCreate):
    return user_service.create_user(body.model_dump())


@router.get("", response_model=Page[UserOut], summary="List users")
def list_users(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return user_service.list_users(limit, offset)


@router.get("/{user_id}", response_model=UserOut, responses=NOT_FOUND, summary="Get a user")
def get_user(user_id: str):
    return user_service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserOut,
              responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
              summary="Edit profile (partial)")
def update_user(user_id: str, body: UserUpdate):
    return user_service.update_user(user_id, body.model_dump(exclude_unset=True))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND,
               summary="Delete a user and all their data")
def delete_user(user_id: str):
    user_service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{user_id}/stats", response_model=UserStats, responses=NOT_FOUND,
            summary="Counts shown on the profile page")
def stats(user_id: str):
    return user_service.get_stats(user_id)


@router.get("/{user_id}/activity", response_model=list[ActivityOut], responses=NOT_FOUND,
            summary="Activity feed (newest first, max 50 kept)")
def activity(user_id: str,
             type: ActivityType | None = Query(None, description="Only this kind of event"),
             limit: int = Query(15, ge=1, le=50)):
    return activity_service.list_activity(user_id, type.value if type else None, limit)


@router.get("/{user_id}/recommendations", response_model=list[RecommendationOut],
            responses=NOT_FOUND, summary="Dishes this user might like next")
def recommendations(user_id: str,
                    limit: int = Query(5, ge=1, le=20),
                    country: str | None = Query(None, description="Only this country id"),
                    category: str | None = Query(None)):
    return recommendation_service.recommend(user_id, limit, country, category)
