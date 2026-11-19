from enum import Enum

from fastapi import APIRouter, Query

from app.schemas.common import ErrorResponse, Page
from app.schemas.dish import DishOut, DishSummary
from app.schemas.review import ReviewOut
from app.services import dish_service, review_service

router = APIRouter(prefix="/dishes", tags=["Dishes"])
NOT_FOUND = {404: {"model": ErrorResponse}}


class DishSort(str, Enum):
    name = "name"
    rating = "rating"
    newest = "newest"


@router.get("", response_model=Page[DishSummary], summary="Search and filter TheMealDB dishes")
def list_dishes(
    q: str | None = Query(None, description="Search by dish name"),
    country: str | None = Query(None, description="Country id, e.g. 'italy'"),
    category: str | None = Query(None, description="TheMealDB category"),
    ingredient: str | None = Query(None, description="TheMealDB ingredient"),
    sort: DishSort = DishSort.name,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return dish_service.list_dishes(q, country, category, ingredient, sort.value, limit, offset)


@router.get("/categories", response_model=list[str], summary="TheMealDB categories")
def categories():
    return dish_service.list_categories()


@router.get("/random", response_model=DishOut, responses=NOT_FOUND, summary="A random TheMealDB dish")
def random_dish(country: str | None = Query(None, description="Limit to one country id")):
    return dish_service.random_dish(country)


@router.get("/{dish_id}", response_model=DishOut, responses=NOT_FOUND, summary="Get TheMealDB dish details")
def get_dish(dish_id: str):
    return dish_service.get_dish(dish_id)


@router.get("/{dish_id}/reviews", response_model=Page[ReviewOut], responses=NOT_FOUND,
            summary="All users' reviews of a dish")
def dish_reviews(dish_id: str, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return review_service.list_dish_reviews(dish_id, limit, offset)
