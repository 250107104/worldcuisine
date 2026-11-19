"""Small helpers that fetch a resource or raise the right domain error."""
from app.core.exceptions import NotFoundError
from app.db import db
from app.services import themealdb


def require_user(user_id: str) -> dict:
    user = db.users.get(user_id)
    if not user:
        raise NotFoundError(f"User '{user_id}' not found")
    return user


def require_dish(dish_id: str) -> dict:
    dish = db.dishes.get(str(dish_id))
    if dish and dish.get("instructions") is not None and dish.get("category") is not None:
        return dish
    dish = themealdb.get_meal(str(dish_id))
    if not dish:
        raise NotFoundError(f"Dish '{dish_id}' not found")
    db.dishes[dish["id"]] = dish
    return dish


def normalize_country_id(country_id: str) -> str:
    return country_id.strip().lower()


def require_country(country_id: str) -> dict:
    country = db.countries.get(normalize_country_id(country_id))
    if not country:
        raise NotFoundError(f"Country '{country_id}' not found")
    return country


def find_review(user_id: str, dish_id: str):
    for review in db.reviews.values():
        if review["user_id"] == user_id and review["dish_id"] == dish_id:
            return review
    return None
