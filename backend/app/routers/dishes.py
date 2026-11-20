from enum import Enum

from fastapi import APIRouter, Query, Response, status

from app.db import DBSession
from app.schemas.common import ErrorResponse, Page
from app.schemas.input import InputText
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
    session: DBSession,
    q: InputText | None = Query(None, description="Part of the dish name"),
    country: InputText | None = Query(None, description="Country id, e.g. 'italy'"),
    category: InputText | None = Query(None, description="Exact category, e.g. 'Dessert'"),
    ingredient: InputText | None = Query(None, description="Part of an ingredient name"),
    sort: DishSort = DishSort.name,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return dish_service.list_dishes(session, q, country, category, ingredient, sort.value, limit, offset)


# Fixed paths must be declared before '/{dish_id}'
@router.get("/categories", response_model=list[str], summary="All dish categories")
def categories(session: DBSession):
    return dish_service.list_categories(session)


@router.get("/random", response_model=DishOut, responses=NOT_FOUND, summary="A random dish")
def random_dish(session: DBSession, country: InputText | None = Query(None, description="Limit to one country id")):
    return dish_service.random_dish(session, country)


@router.post("", response_model=DishOut, status_code=status.HTTP_201_CREATED,
             responses={409: {"model": ErrorResponse}},
             summary="Add a dish to the catalog")
def create_dish(session: DBSession, body: DishCreate):
    return dish_service.create_dish(session, body.model_dump())


@router.get("/{dish_id}", response_model=DishOut, responses=NOT_FOUND, summary="Get one dish")
def get_dish(session: DBSession, dish_id: InputText):
    return dish_service.get_dish(session, dish_id)


@router.patch("/{dish_id}", response_model=DishOut,
              responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
              summary="Update a dish (partial)")
def update_dish(session: DBSession, dish_id: InputText, body: DishUpdate):
    return dish_service.update_dish(session, dish_id, body.model_dump(exclude_unset=True))


@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT,
               responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
               summary="Delete a dish",
               description="Fails with 409 if users rated, reviewed or saved the dish, unless `force=true` "
                           "(which removes it from every user's data).")
def delete_dish(session: DBSession, dish_id: InputText, force: bool = Query(False)):
    dish_service.delete_dish(session, dish_id, force)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{dish_id}/reviews", response_model=Page[ReviewOut], responses=NOT_FOUND,
            summary="All users' reviews of a dish")
def dish_reviews(session: DBSession, dish_id: InputText, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return review_service.list_dish_reviews(session, dish_id, limit, offset)
