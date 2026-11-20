from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.dish import DishSummary
from app.schemas.input import BodyId, RequestBody


class StampOut(BaseModel):
    country_id: str
    name: str
    iso2: str
    explored_at: str | None = Field(description="null = not visited yet")


class PassportOut(BaseModel):
    explored: int
    total: int
    percent: int
    rank: str
    stamps: list[StampOut]


class StampCreate(RequestBody):
    country_id: BodyId = Field(examples=["italy"])


class ExploredOut(BaseModel):
    dish_id: str
    newly_explored: bool


class ActivityType(str, Enum):
    watchlist = "watchlist"
    favorite = "favorite"
    tried = "tried"
    rating = "rating"
    review = "review"


class ActivityOut(BaseModel):
    type: str
    dish_id: str | None
    dish_name: str | None
    detail: int | str | None
    at: str


class RecommendationOut(BaseModel):
    dish: DishSummary
    score: float
    reasons: list[str]
