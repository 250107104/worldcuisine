"""Small cached adapter for TheMealDB's public v1 API."""
from concurrent.futures import ThreadPoolExecutor
from threading import RLock
import time

import httpx

from app.core.exceptions import AppError
from app.db import db

BASE_URL = "https://www.themealdb.com/api/json/v1/1"
CACHE_TTL_SECONDS = 900
_TIMEOUT = 10.0
_cache: dict[str, tuple[float, dict]] = {}
_lock = RLock()


class MealDbError(AppError):
    status_code = 502
    code = "upstream_error"


def _get_json(path: str, **params) -> dict:
    url = f"{BASE_URL}/{path}"
    key = f"{url}?{httpx.QueryParams(params)}"
    now = time.monotonic()
    with _lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]
    try:
        response = httpx.get(url, params=params, timeout=_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("TheMealDB returned a non-object response")
    except (httpx.HTTPError, ValueError) as exc:
        raise MealDbError("TheMealDB is temporarily unavailable") from exc
    with _lock:
        _cache[key] = (now, payload)
    return payload


def _country_for_area(area: str | None) -> dict | None:
    if not area:
        return None
    needle = area.casefold()
    return next((c for c in db.countries.values() if c["cuisine"].casefold() == needle), None)


def normalize_meal(raw: dict, area: str | None = None) -> dict | None:
    """Convert a TheMealDB response to the backend's stable dish representation.

    Filter endpoints omit strArea and recipe details, so callers may provide the
    cuisine area when it is already known (for example filter.php?a=Italian).
    """
    country = _country_for_area(raw.get("strArea") or area)
    meal_id = raw.get("idMeal")
    name = raw.get("strMeal")
    if not country or not meal_id or not name:
        return None
    ingredients = []
    for index in range(1, 21):
        ingredient = (raw.get(f"strIngredient{index}") or "").strip()
        if ingredient:
            ingredients.append({"name": ingredient, "measure": (raw.get(f"strMeasure{index}") or "").strip()})
    tags = [tag.strip() for tag in (raw.get("strTags") or "").split(",") if tag.strip()]
    return {
        "id": str(meal_id), "name": name.strip(), "country_id": country["id"],
        "category": (raw.get("strCategory") or "").strip() or None,
        "image": raw.get("strMealThumb") or None,
        "tags": tags, "ingredients": ingredients,
        "instructions": (raw.get("strInstructions") or "").strip() or None,
        "created_at": None,
    }


def get_by_area(area: str) -> list[dict]:
    raw_meals = _get_json("filter.php", a=area).get("meals") or []
    return [meal for raw in raw_meals if (meal := normalize_meal(raw, area=area))]


def get_filtered_ids(kind: str, value: str) -> set[str]:
    """IDs from TheMealDB category/ingredient filters (these are short records)."""
    rows = _get_json("filter.php", **{kind: value}).get("meals") or []
    return {str(row["idMeal"]) for row in rows if row.get("idMeal")}


def search(name: str) -> list[dict]:
    raw_meals = _get_json("search.php", s=name).get("meals") or []
    return [meal for raw in raw_meals if (meal := normalize_meal(raw))]


def get_meal(meal_id: str) -> dict | None:
    raw_meals = _get_json("lookup.php", i=meal_id).get("meals") or []
    return normalize_meal(raw_meals[0]) if raw_meals else None


def get_random() -> dict | None:
    raw_meals = _get_json("random.php").get("meals") or []
    return normalize_meal(raw_meals[0]) if raw_meals else None


def get_categories() -> list[str]:
    rows = _get_json("list.php", c="list").get("meals") or []
    return sorted(row["strCategory"] for row in rows if row.get("strCategory"))


def area_counts() -> dict[str, int]:
    countries = list(db.countries.values())
    def count(country):
        return country["id"], len(get_by_area(country["cuisine"]))
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(pool.map(count, countries))


def all_catalog_summaries() -> list[dict]:
    countries = list(db.countries.values())
    with ThreadPoolExecutor(max_workers=8) as pool:
        lists = list(pool.map(lambda c: get_by_area(c["cuisine"]), countries))
    by_id = {meal["id"]: meal for meals in lists for meal in meals}
    for meal in by_id.values():
        db.dishes.setdefault(meal["id"], meal)
    return list(by_id.values())


def clear_cache() -> None:
    with _lock:
        _cache.clear()
