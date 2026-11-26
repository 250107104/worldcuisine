from fastapi import APIRouter, Depends, Query, Response, status

from app.db import DBSession
from app.dependencies import require_user_access
from app.schemas.common import ErrorResponse, Page
from app.schemas.input import InputText
from app.schemas.review import RatingIn, RatingOut, ReviewOut, ReviewSort, ReviewUpsert
from app.services import review_service

router = APIRouter(prefix="/users/{user_id}", tags=["Reviews & Ratings"],
                   dependencies=[Depends(require_user_access)])
NOT_FOUND = {404: {"model": ErrorResponse}}
ERR = {404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}}


@router.put("/reviews/{dish_id}", response_model=ReviewOut, responses={**NOT_FOUND, 201: {"model": ReviewOut}},
            summary="Write or edit your review of a dish",
            description="One review per user and dish. Returns 201 when created, 200 when an existing review "
                        "was edited. Also sets your rating, marks the dish as tried and stamps the country.")
def put_review(session: DBSession, user_id: InputText, dish_id: InputText, body: ReviewUpsert, response: Response):
    review, created = review_service.upsert_review(session, user_id, dish_id, body.rating, body.text)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return review


@router.get("/reviews", response_model=Page[ReviewOut], responses=NOT_FOUND, summary="Your reviews")
def list_reviews(session: DBSession, user_id: InputText, min_rating: int | None = Query(None, ge=1, le=5),
                 sort: ReviewSort = ReviewSort.newest,
                 limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return review_service.list_user_reviews(session, user_id, min_rating, sort.value, limit, offset)


@router.get("/reviews/{dish_id}", response_model=ReviewOut, responses=NOT_FOUND, summary="Your review of one dish")
def get_review(session: DBSession, user_id: InputText, dish_id: InputText):
    return review_service.get_review(session, user_id, dish_id)


@router.delete("/reviews/{dish_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND,
               summary="Delete your review (the rating is kept)")
def delete_review(session: DBSession, user_id: InputText, dish_id: InputText):
    review_service.delete_review(session, user_id, dish_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/ratings/{dish_id}", response_model=RatingOut, responses=NOT_FOUND,
            summary="Rate a dish 1-5")
def put_rating(session: DBSession, user_id: InputText, dish_id: InputText, body: RatingIn):
    return review_service.set_rating(session, user_id, dish_id, body.rating)


@router.get("/ratings", response_model=Page[RatingOut], responses=NOT_FOUND, summary="Your ratings")
def list_ratings(session: DBSession, user_id: InputText, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return review_service.list_ratings(session, user_id, limit, offset)


@router.delete("/ratings/{dish_id}", status_code=status.HTTP_204_NO_CONTENT, responses=ERR,
               summary="Remove your rating (409 if the dish has a review)")
def delete_rating(session: DBSession, user_id: InputText, dish_id: InputText):
    review_service.delete_rating(session, user_id, dish_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
