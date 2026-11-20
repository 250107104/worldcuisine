"""Demo account reset. The catalog is imported separately from TheMealDB."""
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import Country, Dish, User


def reset_demo_data(session: Session) -> dict:
    session.execute(text(
        "TRUNCATE activity, passport_stamps, explored_dishes, reviews, ratings, "
        "collection_entries, users RESTART IDENTITY"
    ))
    session.add(User(id="u1", username="Food Explorer", avatar="🍜", bio=""))
    session.flush()
    return {
        "detail": "User data reset. Catalog retained",
        "countries": session.scalar(select(func.count()).select_from(Country)),
        "dishes": session.scalar(select(func.count()).select_from(Dish)),
        "users": session.scalar(select(func.count()).select_from(User)),
    }
