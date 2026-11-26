from fastapi import APIRouter, Depends

from app.db import DBSession
from app.dependencies import require_admin
from app.schemas.common import DemoResetOut
from app.seed import reset_demo_data

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.post("/reset", response_model=DemoResetOut, summary="Reset demo user data and keep the catalog")
def reset_data(session: DBSession):
    return reset_demo_data(session)
