# WorldCuisine API (FastAPI)

REST backend for the WorldCuisine project: explore dishes by country, keep a watchlist / favorites / tried list,
write reviews and ratings, collect Culinary Passport stamps, and get recommendations.
FastAPI serves both the website and its API. The website uses the API for profiles and all personal data.
The FastAPI backend stores its data in PostgreSQL. Restarting FastAPI preserves the database contents.

## Run locally

1. Start PostgreSQL. In pgAdmin, create a database named `worldcuisine` using **Databases → Create → Database**.
2. From the project folder, run the commands below in PowerShell. Open `backend/.env` and replace `YOUR_PASSWORD` with the password for your PostgreSQL user. Adjust the username or port if yours differs. URL-encode reserved characters in the password.
3. Apply the migrations, import the catalog, and run the server. Open [WorldCuisine](http://127.0.0.1:8000/index.html) or [Swagger UI](http://127.0.0.1:8000/docs).

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Edit .env before running the commands below.
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.import_catalog
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

On macOS/Linux, use `python3 -m venv .venv`, `.venv/bin/python` for the Python commands, and `cp .env.example .env`.
A fresh database gets demo user `u1`. The catalog import retrieves countries and recipes from [TheMealDB](https://www.themealdb.com/api.php) and writes them to PostgreSQL. It uses the API's country names and cuisine labels, supplements them with ISO codes from `pycountry`, and links each recipe to its country. The importer uses TheMealDB's country list and A–Z recipe search. Rows without enough data to establish a country or serve a recipe are counted as skipped.

The import uses TheMealDB's educational key `1` by default. You can set `THEMEALDB_API_KEY` in `.env`. Running the import again adds new dishes and updates country labels. It keeps existing dish records and avoids duplicates. An upstream request failure leaves the database unchanged. Once imported, the catalog works without an upstream request when the backend starts or serves a route.

Migrations create an empty catalog. If the first import fails, the catalog stays empty. Run the import command again once TheMealDB is available. Existing databases keep their stored records; use a fresh database if you want to start with an empty catalog.
`POST /admin/reset` resets user data and retains the catalog. Use it only for disposable demo data.

### Website

Use the website served by FastAPI at `http://127.0.0.1:8000/index.html`. Go to **Profile → Create profile**, enter your username, and save.
When you add a dish to the watchlist or favorites or write a review, the website sends the change to FastAPI. Open **Watchlist** or **Reviews** to see the stored results.
Use the same hostname and port when reopening the site so your browser keeps the selected profile ID.

### Automated tests

Create a separate, disposable database named `worldcuisine_test`. Set `TEST_DATABASE_URL` to its PostgreSQL URL and run
`python -m pytest -q` with the environment's Python from `backend`. The suite applies the migration and resets this test database between tests.

## Structure

| Location | Responsibility |
|---|---|
| `app/db.py` | Environment configuration and one SQLAlchemy transaction per request |
| `app/models.py` | ORM tables, relationships, foreign keys and constraints |
| `app/schemas/` | Pydantic request validation and response shapes |
| `app/services/` | Database queries, CRUD and business rules |
| `app/routers/` | Existing FastAPI paths, parameters and status codes |
| `app/import_catalog.py` | TheMealDB catalog import |
| `alembic/versions/` | Reproducible database schema and demo account |
| `tests/` | HTTP and service integration tests with PostgreSQL |

`Country → Dish` is a one-to-many relationship through `dishes.country_id`. Dish ingredients and tags are stored as JSONB recipe fields.
Users and dishes have foreign keys from collections, reviews, ratings, explored recipes and activity. Passport stamps link users to countries.
A review reads its stars from the corresponding rating row, so editing a rating also changes the stars shown on the review.

## Error format
```json
{"detail": "'Spaghetti Carbonara' is already in your watchlist", "code": "conflict"}
```
| Status | Code | When it is returned |
|---|---|---|
| 404 | `not_found` | The requested user, dish, country or related resource does not exist. |
| 409 | `conflict` | A duplicate, protected relationship or retryable concurrent write prevents the operation. |
| 422 | `invalid_reference` | A dish points to a missing country, or PostgreSQL rejects a foreign key. |
| 422 | `validation_error` | A field, body or parameter is invalid, or data violates a PostgreSQL constraint. Pydantic failures include `errors` with the field and message. |
| 503 | `database_unavailable` | The database connection or pool is temporarily unavailable. |
| 405 / 500 | `method_not_allowed` / `server_error` | The method is unsupported or an unexpected error occurred. |

Create and PATCH share field validators. JSON bodies reject unknown fields, blank or too-short required text after trimming
and null characters. Ratings accept whole numbers from 1 to 5 and reject booleans.
PATCH requires at least one field. Use `{"image":null}` to clear a dish image.
A failed write rolls back the entire request, including changes made before a constraint fails.

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
Passport shows stamps for countries in the catalog, percent explored and a rank (Newcomer < Tourist < Traveler <
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
| Admin | `POST /admin/reset` |

`GET /` and `GET /health` are metadata endpoints and do not query PostgreSQL.

## Swagger test script (`/docs`)
Import the catalog before opening Swagger. Expand a route, click **Try it out**, enter the values, and click **Execute**.

| Request | Expected result |
|---|---|
| `GET /countries/italy` | 200 with the imported country name and cuisine |
| `GET /countries/italy/dishes` | 200 with meals from Italy. Copy a `mealdb-...` ID. |
| `GET /dishes/{dish_id}` | 200 with the imported recipe and ingredients |
| `POST /users/u1/collections/watchlist` with `{"dish_id":"<copied id>"}` | 201 on the first request and 409 on a repeat |
| `PUT /users/u1/reviews/{dish_id}` with `{"rating":5,"text":"Simple and delicious."}` | 201 for a new review |
| `GET /users/u1/passport` | 200 with an Italy stamp after the review |
| `DELETE /users/u1/ratings/{dish_id}` | 409 while the review exists |
| `POST /dishes` with the valid body below | 201. Use the returned ID to test PATCH and DELETE. |
| `POST /dishes` with `"country_id":"mars"` in the body below | 422 `invalid_reference` |
| `GET /dishes/missing` | 404 `not_found` |

Valid `POST /dishes` body:
```json
{"name": "Lasagne", "country_id": "italy", "category": "Pasta",
 "ingredients": [{"name": "pasta sheets", "measure": "12"}, {"name": "ragu", "measure": "500 g"}],
 "instructions": "Layer pasta, ragu and bechamel, then bake until bubbling."}
```

### Persistence check

1. In Swagger, send `POST /users` with `{"username":"Restart Demo"}`. Copy the returned `id`.
2. Stop FastAPI with **Ctrl+C** and restart it using the same `.env`.
3. Open Swagger again and send `GET /users/{user_id}` using that ID. Expect `200` with `Restart Demo`. You can repeat with
   `GET /users/u1/reviews/{dish_id}` after the review demo, using the imported dish ID.

## Design notes
- The local demo uses browser-specific profiles. There is no password-based login or account recovery.
- Imported dish IDs use the `mealdb-` prefix followed by TheMealDB’s ID. Local dishes keep their existing ID format.
- The browser stores the current profile ID. PostgreSQL stores the profile, collections, reviews, ratings, and passport. Older browser-only data is not imported.
