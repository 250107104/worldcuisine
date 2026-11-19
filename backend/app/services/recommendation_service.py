"""Personalised suggestions selected from TheMealDB and scored using local user data."""
from app.db import db
from app.services import dish_service, themealdb
from app.services.lookups import require_country, require_user


def recommend(user_id: str, limit: int = 5, country_id=None, category=None) -> list[dict]:
    require_user(user_id)
    candidates = dish_service._candidates(country_id=country_id, category=category)
    cols = db.collections[user_id]
    liked = {dish_id for dish_id, rating in db.ratings[user_id].items() if rating >= 4} | set(cols["favorites"])
    liked_categories = {db.dishes[dish_id]["category"] for dish_id in liked if dish_id in db.dishes}
    liked_countries = {db.dishes[dish_id]["country_id"] for dish_id in liked if dish_id in db.dishes}
    stamped = set(db.stamps[user_id])

    results = []
    for dish in candidates:
        dish_id = dish["id"]
        if dish_id in cols["tried"] or dish_id in cols["watchlist"]:
            continue
        score, reasons = 0.0, []
        country_name = db.countries[dish["country_id"]]["name"]
        if dish["country_id"] not in stamped:
            score += 3
            reasons.append(f"new passport stamp: {country_name}")
        if dish.get("category") in liked_categories:
            score += 2
            reasons.append(f"you like {dish['category']} dishes")
        if dish["country_id"] in liked_countries:
            score += 1
            reasons.append(f"you enjoyed {country_name} cuisine")
        summary = dish_service.to_summary(dish)
        if summary["average_rating"]:
            score += summary["average_rating"] / 5
            reasons.append(f"community rating {summary['average_rating']}/5")
        results.append((score, dish["name"], {"dish": summary, "score": round(score, 2),
                                               "reasons": reasons or ["worth a try"]}))

    results.sort(key=lambda item: (-item[0], item[1].casefold()))
    return [item[2] for item in results[:limit]]
