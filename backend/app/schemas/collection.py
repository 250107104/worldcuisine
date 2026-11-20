from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.dish import DishSummary
from app.schemas.input import BodyId, RequestBody


class CollectionKind(str, Enum):
    watchlist = "watchlist"
    favorites = "favorites"
    tried = "tried"


class CollectionAdd(RequestBody):
    dish_id: BodyId = Field(examples=["1001"])


class CollectionItem(BaseModel):
    dish: DishSummary
    added_at: str


class CollectionSort(str, Enum):
    recent = "recent"
    name = "name"
