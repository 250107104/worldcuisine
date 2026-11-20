from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.constants import MAX_ACTIVITY
from app.models import Activity, Dish
from app.services.lookups import require_user


def log(session: Session, user_id: str, type_: str, dish: Dish, detail: int | None = None) -> None:
    session.add(Activity(user_id=user_id, type=type_, dish_id=dish.id, dish_name=dish.name, detail=detail))
    old_ids = select(Activity.id).where(Activity.user_id == user_id).order_by(Activity.id.desc()).offset(MAX_ACTIVITY)
    session.execute(delete(Activity).where(Activity.id.in_(old_ids)))


def list_activity(session: Session, user_id: str, type_: str | None = None, limit: int = 15) -> list[dict]:
    require_user(session, user_id)
    stmt = select(Activity).where(Activity.user_id == user_id)
    if type_:
        stmt = stmt.where(Activity.type == type_)
    entries = session.scalars(stmt.order_by(Activity.id.desc()).limit(limit))
    return [
        {"type": a.type, "dish_id": a.dish_id, "dish_name": a.dish_name, "detail": a.detail, "at": a.at.isoformat()}
        for a in entries
    ]
