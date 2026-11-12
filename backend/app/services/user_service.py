from app.core.constants import AVATARS
from app.core.exceptions import ConflictError
from app.db import db, utcnow
from app.services.lookups import require_user
from app.services.pagination import paginate


def _check_username(username: str, ignore_id: str | None = None) -> None:
    for u in db.users.values():
        if u["id"] != ignore_id and u["username"].lower() == username.lower():
            raise ConflictError(f"Username '{username}' is already taken")


def create_user(data: dict) -> dict:
    _check_username(data["username"])
    user_id = db.next_id("user")
    user = {"id": user_id, "username": data["username"], "bio": data.get("bio", ""),
            "avatar": data.get("avatar") or AVATARS[0], "created_at": utcnow()}
    db.users[user_id] = user
    db.init_user_data(user_id)
    return user


def list_users(limit: int = 20, offset: int = 0) -> dict:
    return paginate(sorted(db.users.values(), key=lambda u: u["created_at"]), limit, offset)


def get_user(user_id: str) -> dict:
    return require_user(user_id)


def update_user(user_id: str, changes: dict) -> dict:
    user = require_user(user_id)
    if "username" in changes:
        _check_username(changes["username"], ignore_id=user_id)
    user.update(changes)
    return user


def delete_user(user_id: str) -> None:
    require_user(user_id)
    db.drop_user_data(user_id)
    del db.users[user_id]


def get_stats(user_id: str) -> dict:
    require_user(user_id)
    ratings = list(db.ratings[user_id].values())
    cols = db.collections[user_id]
    return {
        "explored": len(db.explored_dishes[user_id]),
        "tried": len(cols["tried"]),
        "reviews": sum(1 for r in db.reviews.values() if r["user_id"] == user_id),
        "favorites": len(cols["favorites"]),
        "watchlist": len(cols["watchlist"]),
        "countries": len(db.stamps[user_id]),
        "rated_count": len(ratings),
        "average_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
    }
