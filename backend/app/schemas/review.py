from enum import Enum

from app.schemas.dish import DishSummary
from pydantic import BaseModel, Field, field_validator


class ReviewSort(str, Enum):
    newest = "newest"
    rating = "rating"


class ReviewUpsert(BaseModel):
    rating: int = Field(ge=1, le=5, description="Whole number of stars, 1-5")
    text: str = Field(min_length=10, max_length=1000, examples=["Rich, creamy and easy to make at home."])

    @field_validator("text")
    @classmethod
    def clean(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Review must be at least 10 characters after trimming")
        return v


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


class RatingIn(BaseModel):
    rating: int = Field(ge=1, le=5)


class RatingOut(BaseModel):
    dish: DishSummary
    rating: int
