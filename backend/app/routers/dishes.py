from enum import Enum

from fastapi import APIRouter, Query, Response, status

from app.schemas.common import ErrorResponse, Page
from app.schemas.dish import DishCreate, DishOut, DishSummary, DishUpdate
from app.schemas.review import ReviewOut
from app.services import dish_service, review_service

router = APIRouter(prefix="/dishes", tags=["Dishes"])
NOT_FOUND = {404: {"model": ErrorResponse}}


class DishSort(str, Enum):
    name = "name"
    rating = "rating"
    newest = "newest"


@router.get("", response_model=Page[DishSummary], summary="Search and filter dishes")
def list_dishes(
    q: str | None = Query(None, description="Part of the dish name"),
    country: str | None = Query(None, description="Country id, e.g. 'italy'"),
    category: str | None = Query(None, description="Exact category, e.g. 'Dessert'"),
    ingredient: str | None = Query(None, description="Part of an ingredient name"),
    sort: DishSort = DishSort.name,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return dish_service.list_dishes(q, country, category, ingredient, sort.value, limit, offset)


# Fixed paths must be declared before '/{dish_id}'
@router.get("/categories", response_model=list[str], summary="All dish categories")
def categories():
    return dish_service.list_categories()


@router.get("/random", response_model=DishOut, responses=NOT_FOUND, summary="A random dish")
def random_dish(country: str | None = Query(None, description="Limit to one country id")):
    return dish_service.random_dish(country)


@router.post("", response_model=DishOut, status_code=status.HTTP_201_CREATED,
             responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
             summary="Add a dish to the catalog")
def create_dish(body: DishCreate):
    return dish_service.create_dish(body.model_dump())


@router.get("/{dish_id}", response_model=DishOut, responses=NOT_FOUND, summary="Get one dish")
def get_dish(dish_id: str):
    return dish_service.get_dish(dish_id)


@router.patch("/{dish_id}", response_model=DishOut,
              responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
              summary="Update a dish (partial)")
def update_dish(dish_id: str, body: DishUpdate):
    return dish_service.update_dish(dish_id, body.model_dump(exclude_unset=True))


@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT,
               responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
               summary="Delete a dish",
               description="Fails with 409 if users rated, reviewed or saved the dish, unless `force=true` "
                           "(which removes it from every user's data).")
def delete_dish(dish_id: str, force: bool = Query(False)):
    dish_service.delete_dish(dish_id, force)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{dish_id}/reviews", response_model=Page[ReviewOut], responses=NOT_FOUND,
            summary="All users' reviews of a dish")
def dish_reviews(dish_id: str, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return review_service.list_dish_reviews(dish_id, limit, offset)
