from app.core.constants import MAX_ACTIVITY
from app.db import db, utcnow
from app.services.lookups import require_user


def log(user_id: str, type_: str, dish: dict | None, detail=None) -> None:
    entry = {
        "type": type_,
        "dish_id": dish["id"] if dish else None,
        "dish_name": dish["name"] if dish else None,
        "detail": detail,
        "at": utcnow(),
    }
    db.activity[user_id] = [entry, *db.activity[user_id]][:MAX_ACTIVITY]


def list_activity(user_id: str, type_: str | None = None, limit: int = 15) -> list[dict]:
    require_user(user_id)
    items = db.activity[user_id]
    if type_:
        items = [a for a in items if a["type"] == type_]
    return items[:limit]
