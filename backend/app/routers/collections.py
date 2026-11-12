from fastapi import APIRouter, Query, Response, status

from app.schemas.collection import CollectionAdd, CollectionItem, CollectionKind, CollectionSort
from app.schemas.common import ErrorResponse, Page
from app.services import collection_service

router = APIRouter(prefix="/users/{user_id}/collections", tags=["Collections"])
ERR = {404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}}


@router.get("/{kind}", response_model=Page[CollectionItem], responses={404: {"model": ErrorResponse}},
            summary="List a user's watchlist, favorites or tried dishes")
def list_items(user_id: str, kind: CollectionKind,
               country: str | None = Query(None, description="Country id"),
               category: str | None = None,
               sort: CollectionSort = CollectionSort.recent,
               limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return collection_service.list_items(user_id, kind.value, country, category, sort.value, limit, offset)


@router.post("/{kind}", response_model=CollectionItem, status_code=status.HTTP_201_CREATED, responses=ERR,
             summary="Add a dish",
             description="Duplicates return 409. A tried dish cannot be added to the watchlist. "
                         "Adding to `tried` removes the dish from the watchlist and stamps its country in the passport.")
def add_item(user_id: str, kind: CollectionKind, body: CollectionAdd):
    return collection_service.add(user_id, kind.value, body.dish_id)


@router.delete("/{kind}/{dish_id}", status_code=status.HTTP_204_NO_CONTENT, responses=ERR,
               summary="Remove a dish",
               description="A tried dish that has a review cannot be removed (409): delete the review first.")
def remove_item(user_id: str, kind: CollectionKind, dish_id: str):
    collection_service.remove(user_id, kind.value, dish_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/watchlist/{dish_id}/move-to-favorites", response_model=CollectionItem, responses=ERR,
             summary="Move a dish from the watchlist to favorites")
def move_to_favorites(user_id: str, dish_id: str):
    return collection_service.move_to_favorites(user_id, dish_id)
