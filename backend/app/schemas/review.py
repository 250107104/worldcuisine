from enum import Enum

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, StringConstraints

from app.schemas.dish import DishSummary
from app.schemas.input import RequestBody, TrimmedText


class ReviewSort(str, Enum):
    newest = "newest"
    rating = "rating"


def _reject_boolean_rating(value):
    if isinstance(value, bool):
        raise ValueError("Rating must be a whole number")
    return value


Stars = Annotated[int, Field(ge=1, le=5), BeforeValidator(_reject_boolean_rating)]
ReviewText = Annotated[TrimmedText, StringConstraints(min_length=10, max_length=1000)]


class RatingIn(RequestBody):
    rating: Stars


class ReviewUpsert(RatingIn):
    text: ReviewText = Field(examples=["Rich, creamy and easy to make at home."])


class ReviewOut(BaseModel):
    id: str
    user_id: str
    username: str
    dish_id: str
    dish_name: str
    rating: int
    text: str
    created_at: str
    updated_at: str


class RatingOut(BaseModel):
    dish: DishSummary
    rating: int
