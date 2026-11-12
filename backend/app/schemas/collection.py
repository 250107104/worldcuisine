from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.schemas.dish import DishSummary


class CollectionKind(str, Enum):
    watchlist = "watchlist"
    favorites = "favorites"
    tried = "tried"


class CollectionAdd(BaseModel):
    dish_id: str = Field(examples=["1001"])

    @field_validator("dish_id")
    @classmethod
    def clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("dish_id cannot be blank")
        return v


class CollectionItem(BaseModel):
    dish: DishSummary
    added_at: str


class CollectionSort(str, Enum):
    recent = "recent"
    name = "name"
