from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, InvalidReferenceError, NotFoundError
from app.models import CollectionEntry, Country, Dish, Rating, Review
from app.services.lookups import normalize_country_id, require_country, require_dish
from app.services.pagination import paginate


def summaries(session: Session, dishes: list[Dish]) -> dict[str, dict]:
    if not dishes:
        return {}
    stmt = select(Rating.dish_id, func.sum(Rating.stars), func.count()).where(
        Rating.dish_id.in_([dish.id for dish in dishes])
    ).group_by(Rating.dish_id)
    stats = {dish_id: (round(total / count, 1), count) for dish_id, total, count in session.execute(stmt)}
    result = {}
    for dish in dishes:
        average, count = stats.get(dish.id, (None, 0))
        result[dish.id] = {
            "id": dish.id, "name": dish.name, "country_id": dish.country_id,
            "country_name": dish.country.name, "category": dish.category, "image": dish.image,
            "average_rating": average, "rating_count": count,
        }
    return result


def to_summary(session: Session, dish: Dish) -> dict:
    return summaries(session, [dish])[dish.id]


def to_detail(session: Session, dish: Dish) -> dict:
    return {**to_summary(session, dish), "tags": dish.tags, "ingredients": dish.ingredients,
            "instructions": dish.instructions, "youtube": dish.youtube, "source": dish.source, "created_at": dish.created_at.isoformat()}


def matching_dishes(session: Session, country_id=None, category=None) -> list[Dish]:
    stmt = select(Dish)
    if country_id:
        stmt = stmt.where(Dish.country_id == country_id)
    dishes = list(session.scalars(stmt.order_by(Dish.created_at, Dish.id)))
    if category:
        dishes = [d for d in dishes if d.category.lower() == category.lower()]
    return dishes


def list_dishes(session: Session, q=None, country_id=None, category=None, ingredient=None,
                sort="name", limit=20, offset=0) -> dict:
    if country_id:
        country_id = require_country(session, country_id).id
    dishes = matching_dishes(session, country_id, category)
    if q:
        dishes = [d for d in dishes if q.lower() in d.name.lower()]
    if ingredient:
        dishes = [d for d in dishes if any(ingredient.lower() in i["name"].lower() for i in d.ingredients)]

    if sort == "rating":
        items = list(summaries(session, dishes).values())
        items.sort(key=lambda s: (s["average_rating"] is None, -(s["average_rating"] or 0), s["name"]))
        return paginate(items, limit, offset)
    if sort == "newest":
        dishes.sort(key=lambda d: d.created_at, reverse=True)
    else:
        dishes.sort(key=lambda d: d.name.lower())
    page = paginate(dishes, limit, offset)
    page["items"] = list(summaries(session, page["items"]).values())
    return page


def list_categories(session: Session) -> list[str]:
    return sorted(session.scalars(select(Dish.category).distinct()))


def get_dish(session: Session, dish_id: str) -> dict:
    return to_detail(session, require_dish(session, dish_id))


def random_dish(session: Session, country_id=None) -> dict:
    stmt = select(Dish)
    if country_id:
        stmt = stmt.where(Dish.country_id == require_country(session, country_id).id)
    dish = session.scalar(stmt.order_by(func.random()).limit(1))
    if dish is None:
        raise NotFoundError("No dishes available")
    return to_detail(session, dish)


def _check_duplicate(session: Session, name: str, country: Country, ignore_id: str | None = None) -> None:
    stmt = select(Dish.id).where(Dish.country_id == country.id, func.lower(Dish.name) == func.lower(name))
    if ignore_id is not None:
        stmt = stmt.where(Dish.id != ignore_id)
    duplicate_id = session.scalar(stmt)
    if duplicate_id is not None:
        raise ConflictError(f"'{name}' already exists in {country.name} (dish id {duplicate_id})")


def _target_country(session: Session, country_id: str) -> Country:
    country = session.get(Country, normalize_country_id(country_id))
    if country is None:
        raise InvalidReferenceError(f"Country '{country_id}' does not exist")
    return country


def create_dish(session: Session, data: dict) -> dict:
    country = _target_country(session, data["country_id"])
    _check_duplicate(session, data["name"], country)
    fields = {key: value for key, value in data.items() if key != "country_id"}
    dish = Dish(**fields, country=country)
    session.add(dish)
    session.flush()
    return to_detail(session, dish)


def update_dish(session: Session, dish_id: str, changes: dict) -> dict:
    dish = require_dish(session, dish_id, lock=True)
    country_id = changes.get("country_id")
    country = _target_country(session, country_id) if country_id is not None else dish.country
    if country.id != dish.country_id:
        tried_by = session.scalar(select(func.count()).select_from(CollectionEntry).where(
            CollectionEntry.dish_id == dish_id, CollectionEntry.kind == "tried"
        ))
        if tried_by:
            raise ConflictError(
                f"{tried_by} user(s) already tried this dish, so its country cannot be changed "
                "(their passport stamps depend on it)"
            )
    _check_duplicate(session, changes.get("name", dish.name), country, ignore_id=dish_id)
    for key, value in changes.items():
        if key != "country_id":
            setattr(dish, key, value)
    dish.country = country
    session.flush()
    return to_detail(session, dish)


def delete_dish(session: Session, dish_id: str, force: bool = False) -> None:
    dish = require_dish(session, dish_id, lock=True)
    if not force:
        reviews, ratings, saved = session.execute(select(
            select(func.count()).select_from(Review).where(Review.dish_id == dish_id).scalar_subquery(),
            select(func.count()).select_from(Rating).where(Rating.dish_id == dish_id).scalar_subquery(),
            select(func.count()).select_from(CollectionEntry).where(CollectionEntry.dish_id == dish_id).scalar_subquery(),
        )).one()
        if reviews or ratings or saved:
            raise ConflictError(
                f"Dish is still used by users ({reviews} reviews, {ratings} ratings, "
                f"{saved} saved entries). Retry with ?force=true to delete it everywhere."
            )
    session.delete(dish)
