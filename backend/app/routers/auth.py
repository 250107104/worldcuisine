from fastapi import APIRouter, status

from app.db import DBSession
from app.schemas.common import ErrorResponse
from app.schemas.user import LoginRequest, RegistrationCreate, TokenOut, UserOut
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


@router.post(
    "/login",
    response_model=TokenOut,
    responses={401: {"model": ErrorResponse}},
    summary="Authenticate and receive a JWT access token",
)
def login(session: DBSession, body: LoginRequest):
    user = user_service.authenticate_user(session, str(body.email), body.password)
    token, expires_in = user_service.issue_access_token(user)
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in}
