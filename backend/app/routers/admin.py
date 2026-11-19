from fastapi import APIRouter

from app.db import db
from app.seed import load_seed
from app.services.themealdb import clear_cache

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/reset", summary="Reset local user data and clear the TheMealDB response cache")
def reset_data():
    db.reset()
    clear_cache()
    load_seed(db)
    return {"detail": "Local data reset; catalog is fetched from TheMealDB on demand",
            "countries": len(db.countries), "dishes": 0, "users": len(db.users)}
