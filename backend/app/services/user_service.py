from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import AVATARS
from app.core.exceptions import ConflictError
from app.models import CollectionEntry, ExploredDish, PassportStamp, Rating, Review, User
from app.security import hash_password
from app.services.lookups import require_user


def _view(user: User) -> dict:
    return {"id": user.id, "username": user.username, "bio": user.bio, "avatar": user.avatar,
            "created_at": user.created_at.isoformat()}


def _check_username(session: Session, username: str, ignore_id: str | None = None) -> None:
    stmt = select(User.id).where(func.lower(User.username) == func.lower(username))
    if ignore_id is not None:
        stmt = stmt.where(User.id != ignore_id)
    if session.scalar(stmt) is not None:
        raise ConflictError(f"Username '{username}' is already taken")


def _check_email(session: Session, email: str | None, ignore_id: str | None = None) -> None:
    if email is None:
        return
    stmt = select(User.id).where(func.lower(User.email) == email.lower())
    if ignore_id is not None:
        stmt = stmt.where(User.id != ignore_id)
    if session.scalar(stmt) is not None:
        raise ConflictError("An account with this email already exists")


def create_user(session: Session, data: dict) -> dict:
    _check_username(session, data["username"])
    _check_email(session, data.get("email"))
    user = User(
        username=data["username"], email=data.get("email"),
        password_hash=hash_password(data["password"]) if data.get("password") else None,
        bio=data.get("bio", ""), avatar=data.get("avatar") or AVATARS[0],
    )
    session.add(user)
    session.flush()
    return _view(user)


def list_users(session: Session, limit: int = 20, offset: int = 0) -> dict:
    total = session.scalar(select(func.count()).select_from(User))
    items = session.scalars(select(User).order_by(User.created_at, User.id).limit(limit).offset(offset))
    return {"items": [_view(user) for user in items], "total": total, "limit": limit, "offset": offset}


def get_user(session: Session, user_id: str) -> dict:
    return _view(require_user(session, user_id))


def update_user(session: Session, user_id: str, changes: dict) -> dict:
    user = require_user(session, user_id, lock=True)
    if "username" in changes:
        _check_username(session, changes["username"], ignore_id=user_id)
    if "email" in changes:
        _check_email(session, changes["email"], ignore_id=user_id)
    if "password" in changes:
        user.password_hash = hash_password(changes.pop("password"))
    for key, value in changes.items():
        setattr(user, key, value)
    return _view(user)


def delete_user(session: Session, user_id: str) -> None:
    session.delete(require_user(session, user_id, lock=True))


def get_stats(session: Session, user_id: str) -> dict:
    require_user(session, user_id)
    counts = dict(session.execute(select(CollectionEntry.kind, func.count())
                                .where(CollectionEntry.user_id == user_id).group_by(CollectionEntry.kind)).all())
    total, rated_count = session.execute(
        select(func.sum(Rating.stars), func.count()).where(Rating.user_id == user_id)
    ).one()
    explored, reviews, countries = session.execute(select(
        select(func.count()).select_from(ExploredDish).where(ExploredDish.user_id == user_id).scalar_subquery(),
        select(func.count()).select_from(Review).where(Review.user_id == user_id).scalar_subquery(),
        select(func.count()).select_from(PassportStamp).where(PassportStamp.user_id == user_id).scalar_subquery(),
    )).one()
    return {"explored": explored, "tried": counts.get("tried", 0), "reviews": reviews,
            "favorites": counts.get("favorites", 0), "watchlist": counts.get("watchlist", 0),
            "countries": countries, "rated_count": rated_count,
            "average_rating": round(total / rated_count, 1) if rated_count else None}
