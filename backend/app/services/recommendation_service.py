"""Personalised dish suggestions.

Candidates: dishes the user has not tried and has not put on the watchlist.
Score:
  +3    dish is from a country with no passport stamp yet (would add a stamp)
  +2    category matches a dish the user rated 4-5 or favorited
  +1    country matches a dish the user rated 4-5 or favorited
  +x    community average rating / 5  (0 to 1)
"""
from app.db import db
from app.services import dish_service
from app.services.lookups import require_country, require_user


def recommend(user_id: str, limit: int = 5, country_id=None, category=None) -> list[dict]:
    require_user(user_id)
    if country_id:
        country_id = require_country(country_id)["id"]

    cols = db.collections[user_id]
    liked = {d for d, r in db.ratings[user_id].items() if r >= 4} | set(cols["favorites"])
    liked_categories = {db.dishes[d]["category"] for d in liked}
    liked_countries = {db.dishes[d]["country_id"] for d in liked}
    stamped = set(db.stamps[user_id])

    results = []
    for dish in db.dishes.values():
        if dish["id"] in cols["tried"] or dish["id"] in cols["watchlist"]:
            continue
        if country_id and dish["country_id"] != country_id:
            continue
        if category and dish["category"].lower() != category.lower():
            continue

        score, reasons = 0.0, []
        country_name = db.countries[dish["country_id"]]["name"]
        if dish["country_id"] not in stamped:
            score += 3
            reasons.append(f"new passport stamp: {country_name}")
        if dish["category"] in liked_categories:
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

    results.sort(key=lambda t: (-t[0], t[1]))
    return [r[2] for r in results[:limit]]
