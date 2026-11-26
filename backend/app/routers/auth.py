from fastapi import APIRouter, status

from app.db import DBSession
from app.schemas.common import ErrorResponse
from app.schemas.user import RegistrationCreate, UserOut
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
    summary="Register a new account",
)
def register(session: DBSession, body: RegistrationCreate):
    # Pass the raw password only to the service, which hashes it before persistence.
    return user_service.create_user(session, {
        "username": body.username,
        "email": str(body.email),
        "password": body.password,
        "bio": body.bio,
        "avatar": body.avatar,
    })
