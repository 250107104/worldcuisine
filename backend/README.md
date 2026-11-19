# WorldCuisine backend

FastAPI API with a TheMealDB-backed dish catalog and SQLAlchemy persistence for supported countries, cached dish records and user data (users, collections, ratings, reviews, passport stamps, explored dishes and activity).

## Configure PostgreSQL

Create a PostgreSQL database named `worldcuisine`, then configure the connection before starting the API:

```bash
export DATABASE_URL='postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@localhost:5432/worldcuisine'
```

Install and migrate:

```bash
cd backend
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

For local tests/development without PostgreSQL, the app defaults to `sqlite:///./worldcuisine.db`; set `DATABASE_URL` to use PostgreSQL. Tables are created by the initial Alembic migration (the app also ensures tables exist on startup). The app initializes supported country metadata and a demo account once, only when the database has no countries.

## API and data

Open `http://127.0.0.1:8000/docs`. Dish list/details come from TheMealDB and use its `idMeal` IDs. Responses are cached in memory by the upstream adapter for 15 minutes; details and user-linked dishes are saved locally to preserve relationships. Country-to-cuisine and ISO metadata is a local reference mapping because TheMealDB exposes cuisine areas, not country records.

PostgreSQL persists users, one-to-many user collections/reviews/activity, ratings, passport stamps and explored dishes. Foreign keys, unique constraints and rating/kind checks protect data integrity. Existing service-layer business rules and API routes are retained. User-specific data survives backend restarts; `/admin/reset` is for testing and clears local application data.

## Tests

```bash
pytest
```
