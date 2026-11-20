"""Personalised suggestions based on passport, favorites and ratings."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CollectionEntry, Dish, PassportStamp, Rating
from app.services import dish_service
from app.services.lookups import require_country, require_user


def recommend(session: Session, user_id: str, limit: int = 5, country_id=None, category=None) -> list[dict]:
    require_user(session, user_id)
    if country_id:
        country_id = require_country(session, country_id).id

    entries = session.execute(select(CollectionEntry.dish_id, CollectionEntry.kind)
                              .where(CollectionEntry.user_id == user_id))
    liked = set(session.scalars(select(Rating.dish_id).where(Rating.user_id == user_id, Rating.stars >= 4)))
    excluded = set()
    for dish_id, kind in entries:
        if kind == "favorites":
            liked.add(dish_id)
        else:
            excluded.add(dish_id)
    preferences = list(session.execute(select(Dish.category, Dish.country_id).where(Dish.id.in_(liked))))
    liked_categories = {category for category, _ in preferences}
    liked_countries = {country for _, country in preferences}
    stamped = set(session.scalars(select(PassportStamp.country_id).where(PassportStamp.user_id == user_id)))

    dishes = [dish for dish in dish_service.matching_dishes(session, country_id, category) if dish.id not in excluded]
    summaries = dish_service.summaries(session, dishes)
    results = []
    for dish in dishes:
        score, reasons = 0.0, []
        country_name = dish.country.name
        if dish.country_id not in stamped:
            score += 3
            reasons.append(f"new passport stamp: {country_name}")
        if dish.category in liked_categories:
            score += 2
            reasons.append(f"you like {dish.category} dishes")
        if dish.country_id in liked_countries:
            score += 1
            reasons.append(f"you enjoyed {country_name} cuisine")
        summary = summaries[dish.id]
        if summary["average_rating"]:
            score += summary["average_rating"] / 5
            reasons.append(f"community rating {summary['average_rating']}/5")
        results.append((score, dish.name, {"dish": summary, "score": round(score, 2),
                                          "reasons": reasons or ["worth a try"]}))

    results.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in results[:limit]]
