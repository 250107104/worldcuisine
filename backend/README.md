# WorldCuisine API (FastAPI)

REST backend for the WorldCuisine project: explore dishes by country, keep a watchlist / favorites / tried list,
write reviews and ratings, collect Culinary Passport stamps, and get recommendations.
It ports the rules that `js/storage.js` kept in LocalStorage into a server, and adds multi-user support.
All data is **in memory** and resets to a seed on every start.

## Run
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open **http://127.0.0.1:8000/docs** (Swagger UI). A demo user `u1` and 27 dishes in 29 countries exist from the start.
`POST /admin/reset` puts the data back to the seed at any time (handy between test rounds).

Automated tests (optional, extra to the Swagger testing): `pytest`

## Structure
```
app/
  main.py          app setup, CORS, error handlers (one JSON error format), router registration
  db.py            in-memory store (plain dicts) + id generation
  seed.py          countries (from js/data.js) and starter dishes
  core/            constants and domain exceptions (NotFound 404, Conflict 409, InvalidReference 422)
  schemas/         Pydantic request/response models and validation
  services/        ALL business logic (no FastAPI imports): dish, user, collection, review,
                   passport, activity, recommendation
  routers/         thin FastAPI routers: parse request -> call service -> return result
tests/             test_services.py (logic only) and test_api.py (HTTP, status codes)
```
Routes never contain business rules; services raise domain errors; `main.py` maps them to HTTP responses.

## Error format
```json
{"detail": "'Spaghetti Carbonara' is already in your watchlist", "code": "conflict"}
```
`code` is one of `not_found` (404), `conflict` (409), `invalid_reference` (422), `validation_error` (422,
also lists `errors: [{field, message}]`), `method_not_allowed` (405), `server_error` (500).

## Conventions
**Paging.** Every list endpoint (`/dishes`, `/countries/{id}/dishes`, `/dishes/{id}/reviews`, `/users`,
`/users/{id}/collections/{kind}`, `/users/{id}/reviews`, `/users/{id}/ratings`) takes `limit` (1-100, default 20) and
`offset` (>= 0) and returns the same shape:
```json
{"items": [...], "total": 42, "limit": 20, "offset": 0}
```
`total` counts all matches before paging. `/activity` and `/recommendations` are short "top N" lists and keep a plain
`limit` and a plain array.

**Country ids are case-insensitive.** `italy`, `Italy` and `ITALY` all work in paths, query parameters and request
bodies; they are stored in lowercase.

**Enum parameters.** `sort` (dishes, collections, reviews) and `type` (activity) are enums, so Swagger shows a dropdown
and any other value is a 422.

## The three main workflows

### 1. Collections: watchlist, favorites, tried  (`/users/{id}/collections/{kind}`)
Rules: no duplicates (409) · a tried dish cannot go on the watchlist (409) · marking a dish **tried** removes it from
the watchlist and stamps its country in the passport · a tried dish with a review cannot be removed (409) ·
`move-to-favorites` only works for watchlist dishes (404 otherwise, 409 if already a favorite).

### 2. Reviews and ratings  (`/users/{id}/reviews`, `/ratings`, `/dishes/{id}/reviews`)
Rules: one review per user and dish (`PUT` creates with 201, edits with 200) · writing a review **auto-marks the dish
tried** (leaves watchlist, stamps country) · review stars and rating always stay equal · a rating cannot be deleted
while a review exists (409) · deleting a review keeps the rating · dishes expose a community `average_rating`.

### 3. Culinary Passport, activity and recommendations  (`/users/{id}/passport`, `/activity`, `/recommendations`)
Passport shows stamps for all 29 countries, percent explored and a rank (Newcomer < Tourist < Traveler <
Globetrotter < World Chef). Stamps come automatically from tried/reviewed dishes or manually (409 if repeated; a stamp
earned by a tried dish cannot be removed). Recommendations score untried dishes: +3 new country, +2 liked category,
+1 liked country, + community rating; each result lists its `reasons`.

Also: catalog CRUD (`/dishes`, with duplicate check), users CRUD (unique username, cascade delete), and `/countries`.

Catalog rules that protect the other resources:
- `DELETE /dishes/{id}` returns 409 while users reference the dish. With `?force=true` it removes the dish from every
  review, rating, collection and activity feed. Passport stamps are **kept**: a stamp is a record of a country the user
  explored, and the user can still remove it by hand.
- `PATCH /dishes/{id}` cannot change `country_id` (409) once any user has tried the dish, because their passport stamps
  were earned through that country. Dishes nobody tried can be moved; other fields can always be edited.

## Endpoint overview
| Area | Endpoints |
|---|---|
| Countries | `GET /countries` · `GET /countries/{id}` · `GET /countries/{id}/dishes` (paged) |
| Dishes | `GET /dishes` (q, country, category, ingredient, sort, limit, offset) · `GET /dishes/categories` · `GET /dishes/random` · `GET/PATCH/DELETE /dishes/{id}` · `POST /dishes` · `GET /dishes/{id}/reviews` |
| Users | `POST /users` · `GET /users` (paged) · `GET/PATCH/DELETE /users/{id}` · `GET .../stats` · `GET .../activity` · `GET .../recommendations` |
| Collections | `GET` (paged) `/POST /users/{id}/collections/{watchlist\|favorites\|tried}` · `DELETE .../{kind}/{dish_id}` · `POST .../watchlist/{dish_id}/move-to-favorites` |
| Reviews & ratings | `PUT/GET/DELETE /users/{id}/reviews/{dish_id}` · `GET .../reviews` (paged) · `PUT/DELETE /users/{id}/ratings/{dish_id}` · `GET .../ratings` (paged) |
| Passport | `GET .../passport` · `POST .../passport/stamps` · `DELETE .../passport/stamps/{country_id}` · `POST .../explored-dishes/{dish_id}` |
| Misc | `GET /` · `GET /health` · `POST /admin/reset` |

## Swagger test script (`/docs`)
Start with `POST /admin/reset`. Seeded dish ids: `1001` Carbonara, `1002` Margherita, `1003` Teriyaki (Japan), `1007` Butter Chicken ...

| # | Request | Expect |
|---|---|---|
| 1 | `GET /dishes?country=italy` | 200, `total: 2` |
| 2 | `GET /dishes?limit=0` | 422 `validation_error` |
| 3 | `GET /dishes?country=atlantis` | 404 |
| 4 | `POST /dishes` valid body (see below) | 201 |
| 5 | repeat step 4 | 409 duplicate |
| 6 | `POST /dishes` with `"country_id": "mars"` | 422 `invalid_reference` |
| 7 | `PATCH /dishes/{id}` body `{}` | 422 |
| 8 | `POST /users` `{"username": "Maria"}` then again with `"maria"` | 201, then 409 |
| 9 | `POST /users/u1/collections/watchlist` `{"dish_id":"1001"}` twice | 201, then 409 |
| 10 | `POST /users/u1/collections/watchlist/1001/move-to-favorites` | 200; watchlist now has `total: 0` |
| 11 | `POST /users/u1/collections/tried` `{"dish_id":"1003"}` | 201; `GET .../passport` shows Japan stamped |
| 12 | `POST /users/u1/collections/watchlist` `{"dish_id":"1003"}` | 409 already tried |
| 13 | `PUT /users/u1/reviews/1001` `{"rating":5,"text":"Creamy and perfect carbonara."}` | 201 (again: 200) |
| 14 | `PUT /users/u1/reviews/1001` `{"rating":6,"text":"short"}` | 422 |
| 15 | `PUT /users/u1/ratings/1001` `{"rating":2}` then `GET .../reviews/1001` | review rating is 2 |
| 16 | `DELETE /users/u1/ratings/1001` and `DELETE .../collections/tried/1001` | both 409 (review exists) |
| 17 | `DELETE /dishes/1001` | 409; with `force=true` 204 |
| 18 | `POST /users/u1/passport/stamps` `{"country_id":"france"}` twice | 201, then 409 |
| 19 | `GET /users/u1/recommendations?limit=3` | 3 items with `reasons` |
| 20 | `GET /users/u1/activity?type=review` / `?type=x` | 200 list / 422 (pick `type` from the dropdown) |
| 21 | `DELETE /users/{id}` then `GET /users/{id}` | 204, then 404 |
| 22 | `GET /dishes?country=Italy` | 200, `total: 2` (case does not matter) |
| 23 | `POST /users/u1/collections/tried` `{"dish_id":"1003"}`, then `PATCH /dishes/1003` `{"country_id":"china"}` | 409 (dish was tried); the same PATCH on untried dish `1002` with `"spain"` gives 200 |
| 24 | `GET /users?limit=1&offset=0`, then `GET /users?limit=0` | 200 `{items, total, limit, offset}`, then 422 |
| 25 | `GET /users/u1/reviews?sort=alphabet` | 422 (only `newest` or `rating`) |

Valid `POST /dishes` body:
```json
{"name": "Lasagne", "country_id": "italy", "category": "Pasta",
 "ingredients": [{"name": "pasta sheets", "measure": "12"}, {"name": "ragu", "measure": "500 g"}],
 "instructions": "Layer pasta, ragu and bechamel, then bake until bubbling."}
```

## Design notes
- Auth is out of scope: the user id is part of the URL (`/users/{user_id}/...`).
- Ids are strings (`"1001"`, `"u1"`, `"r1"`) like TheMealDB ids in the frontend.
- The frontend still uses TheMealDB + LocalStorage. CORS is open so it can be switched to this API later.
