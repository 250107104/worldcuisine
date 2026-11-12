from fastapi import APIRouter

from app.db import db
from app.seed import load_seed

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/reset", summary="Reset all data to the starting seed (for testing)")
def reset_data():
    db.reset()
    load_seed(db)
    return {"detail": "Data reset to seed", "countries": len(db.countries),
            "dishes": len(db.dishes), "users": len(db.users)}
