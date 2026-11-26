from fastapi import APIRouter, Depends

from app.db import DBSession
from app.dependencies import get_current_user
from app.schemas.common import DemoResetOut
from app.seed import reset_demo_data

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(get_current_user)])


@router.post("/reset", response_model=DemoResetOut, summary="Reset demo user data and keep the catalog")
def reset_data(session: DBSession):
    return reset_demo_data(session)
