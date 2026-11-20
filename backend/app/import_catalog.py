"""Import the country and recipe catalog from TheMealDB into PostgreSQL."""
import os
import re
import string
from collections import defaultdict
from urllib.parse import quote

import httpx
import pycountry
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Country, Dish

COUNTRY_ALIASES = {
    "British Virgin Islands": "VG", "Cape Verde": "CV", "DR Congo": "CD",
    "Ivory Coast": "CI", "Republic of the Congo": "CG", "South Korea": "KR",
    "North Korea": "KP", "Vietnam": "VN", "Laos": "LA", "Russia": "RU",
    "Iran": "IR", "Syria": "SY", "Taiwan": "TW", "Tanzania": "TZ",
    "Venezuela": "VE", "Palestine": "PS", "Moldova": "MD", "Brunei": "BN",
}
EXISTING_COUNTRY_IDS = {"GB": "uk", "US": "usa"}


class CatalogError(Exception):
    pass


def clean(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def fetch_rows(client: httpx.Client, endpoint: str, **params) -> list[dict]:
    try:
        response = client.get(endpoint, params=params)
        response.raise_for_status()
        rows = response.json()["meals"]
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise CatalogError(f"TheMealDB request failed for {endpoint}. Check connectivity and retry.") from exc
    if rows is None:
        return []
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise CatalogError(f"TheMealDB returned an unexpected response for {endpoint}.")
    return rows


def country_fields(name: str, area: str) -> dict | None:
    try:
        code = pycountry.countries.lookup(COUNTRY_ALIASES.get(name, name))
    except LookupError:
        return None

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug or len(slug) > 32:
        slug = code.alpha_2.lower()
    return {"id": EXISTING_COUNTRY_IDS.get(code.alpha_2, slug), "iso2": code.alpha_2.lower(),
            "iso3": code.alpha_3, "name": name, "cuisine": area}


def recipe_fields(row: dict, country_id: str) -> dict | None:
    external_id = clean(row.get("idMeal"))
    name = clean(row.get("strMeal"))
    category = clean(row.get("strCategory"))
    instructions = clean(row.get("strInstructions"))
    if not re.fullmatch(r"[0-9]{1,24}", external_id) or not name or not category or not instructions:
        return None

    ingredients = []
    for index in range(1, 21):
        ingredient = clean(row.get(f"strIngredient{index}"))
        if ingredient:
            ingredients.append({"name": ingredient, "measure": clean(row.get(f"strMeasure{index}"))})
    tags = (tag.strip() for tag in clean(row.get("strTags")).split(","))
    return {"id": f"mealdb-{external_id}", "name": name, "country_id": country_id,
            "category": category, "instructions": instructions, "image": clean(row.get("strMealThumb")) or None,
            "youtube": clean(row.get("strYoutube")) or None, "source": clean(row.get("strSource")) or None,
            "ingredients": ingredients, "tags": list(dict.fromkeys(tag for tag in tags if tag))}


def import_catalog(engine, client: httpx.Client) -> dict:
    """Fetch first so a partial network failure cannot change the stored catalog."""
    countries = fetch_rows(client, "list.php", a="list")
    if not countries:
        raise CatalogError("TheMealDB returned an empty country list.")
    recipes = [row for letter in string.ascii_lowercase for row in fetch_rows(client, "search.php", f=letter)]
    if not recipes:
        raise CatalogError("TheMealDB returned an empty recipe catalog.")

    country_ids = {}
    countries_by_area = defaultdict(set)
    unmatched_countries = 0
    inserted = skipped = 0
    with Session(engine) as session, session.begin():
        for row in countries:
            name, area = clean(row.get("strCountry")), clean(row.get("strArea"))
            if not name or not area:
                unmatched_countries += 1
                continue
            fields = country_fields(name, area)
            if fields is None:
                unmatched_countries += 1
                continue
            stmt = insert(Country).values(**fields).on_conflict_do_update(
                index_elements=[Country.iso2], set_={"name": name, "cuisine": area}
            ).returning(Country.id)
            country_id = session.scalar(stmt)
            country_ids[name.casefold()] = country_id
            countries_by_area[area.casefold()].add(country_id)

        for row in recipes:
            country_name = clean(row.get("strCountry"))
            country_id = country_ids.get(country_name.casefold())
            if not country_name:
                matches = countries_by_area.get(clean(row.get("strArea")).casefold(), set())
                if len(matches) == 1:
                    country_id = next(iter(matches))
            fields = recipe_fields(row, country_id) if country_id else None
            if fields is None:
                skipped += 1
                continue
            stmt = insert(Dish).values(**fields).on_conflict_do_nothing().returning(Dish.id)
            if session.scalar(stmt) is not None:
                inserted += 1
            else:
                existing = session.get(Dish, fields["id"])
                if existing is not None:
                    existing.youtube = fields["youtube"]
                    existing.source = fields["source"]

    return {"countries": len(set(country_ids.values())), "dishes_added": inserted,
            "dishes_already_present_or_conflicting": len(recipes) - inserted - skipped,
            "unmatched_country_rows": unmatched_countries, "skipped_dishes": skipped}


def main() -> None:
    engine = get_engine()
    key = quote(os.getenv("THEMEALDB_API_KEY", "1"), safe="")
    with httpx.Client(base_url=f"https://www.themealdb.com/api/json/v1/{key}/",
                      timeout=15, follow_redirects=True) as client:
        try:
            result = import_catalog(engine, client)
        except CatalogError as exc:
            raise SystemExit(str(exc)) from exc
    print("\n".join(f"{field}: {value}" for field, value in result.items()))


if __name__ == "__main__":
    main()
