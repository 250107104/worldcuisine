"""Dependencies shared by protected API endpoints."""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import DBSession
from app.models import User
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    session: DBSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    """Validate the Bearer JWT and resolve its subject to an active user."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        claims = decode_access_token(credentials.credentials)
    except (jwt.PyJWTError, ValueError, TypeError):
        raise _unauthorized() from None
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise _unauthorized()
    user = session.get(User, subject)
    if user is None:
        raise _unauthorized()
    return user


def require_user_access(
    user_id: str,
    current_user: User = Depends(get_current_user),
) -> User:
    """Require that a user-scoped route is accessed by that same account."""
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access another user's data")
    return current_user


CurrentUser = Depends(get_current_user)
