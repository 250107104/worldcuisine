from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    name: str
    measure: str = ""


class DishSummary(BaseModel):
    id: str
    name: str
    country_id: str
    country_name: str
    category: str | None
    image: str | None
    average_rating: float | None = Field(description="Average of local user ratings, null if unrated")
    rating_count: int


class DishOut(DishSummary):
    tags: list[str]
    ingredients: list[Ingredient]
    instructions: str | None
    created_at: str | None
