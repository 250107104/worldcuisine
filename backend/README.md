# WorldCuisine backend

FastAPI REST API for user-specific collections, reviews, ratings, activity and Culinary Passport progress. The meal catalog is fetched from TheMealDB; the backend keeps country-to-cuisine metadata locally because TheMealDB exposes cuisine areas (such as `Italian`), not country records.

## Run

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. `pytest` runs the automated tests. The API requires internet access when catalog endpoints are used. Upstream data is cached in memory for 15 minutes; user state is currently in memory too and resets on restart. `POST /admin/reset` clears local state and the upstream response cache.

## Data flow

- `GET /countries` returns the supported country/cuisine mapping and live TheMealDB dish counts.
- `/dishes` calls TheMealDB search, area, category, ingredient, lookup and random endpoints. Dish IDs are the upstream `idMeal` values; details are fetched by `lookup.php` as needed.
- Ratings, reviews, watchlists, favorites, tried dishes and passport stamps are WorldCuisine data held by the backend. Country metadata (stable URL ID and ISO codes) is configuration, not a local dish catalog.
- TheMealDB failures return `502` with `{"code":"upstream_error"}`. Cached responses can still be served until the cache expires.

## Main endpoints

- Countries: `GET /countries`, `GET /countries/{id}`, `GET /countries/{id}/dishes`
- TheMealDB catalog: `GET /dishes` (q, country, category, ingredient, sort, limit, offset), `GET /dishes/categories`, `GET /dishes/random`, `GET /dishes/{id}`
- Users: `POST/GET /users`, `GET/PATCH/DELETE /users/{id}`
- User collections: `/users/{id}/collections/{watchlist|favorites|tried}`
- Reviews and ratings: `/users/{id}/reviews`, `/users/{id}/ratings`, `/dishes/{id}/reviews`
- Passport, activity, recommendations: `/users/{id}/passport`, `/users/{id}/activity`, `/users/{id}/recommendations`

The catalog is read-only through this API: adding, editing or deleting a dish would incorrectly suggest that the backend can modify TheMealDB's source records. User-specific ratings and saves continue to reference the upstream meal ID.
