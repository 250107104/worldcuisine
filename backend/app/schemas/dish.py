from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

from app.schemas.input import BodyId, InputText, PatchBody, RequestBody, TrimmedText


class Ingredient(RequestBody):
    name: Annotated[TrimmedText, StringConstraints(min_length=1, max_length=60)]
    measure: Annotated[TrimmedText, StringConstraints(max_length=40)] = ""


def _check_ingredient_names(ingredients: list[Ingredient]) -> list[Ingredient]:
    names = {ingredient.name.lower() for ingredient in ingredients}
    if len(names) != len(ingredients):
        raise ValueError("Ingredient names must be unique")
    return ingredients


def _clean_tags(tags: list[str]) -> list[str]:
    return list(dict.fromkeys(tag for tag in tags if tag))


DishName = Annotated[TrimmedText, StringConstraints(min_length=2, max_length=100)]
DishCategory = Annotated[TrimmedText, StringConstraints(min_length=2, max_length=40)]
Instructions = Annotated[TrimmedText, StringConstraints(min_length=10, max_length=5000)]
Ingredients = Annotated[list[Ingredient], Field(min_length=1, max_length=40), AfterValidator(_check_ingredient_names)]
Tags = Annotated[list[TrimmedText], Field(max_length=10), AfterValidator(_clean_tags)]
ImageUrl = Annotated[InputText, StringConstraints(pattern=r"^https?://[^/\s?#]+\S*$")]


class DishCreate(RequestBody):
    name: DishName = Field(examples=["Lasagne"])
    country_id: BodyId = Field(examples=["italy"])
    category: DishCategory = Field(examples=["Pasta"])
    ingredients: Ingredients
    instructions: Instructions
    tags: Tags = Field(default_factory=list)
    image: ImageUrl | None = Field(default=None, description="http(s) URL")


class DishUpdate(PatchBody):
    """PATCH body: send only the fields you want to change."""
    nullable_fields = frozenset({"image"})

    name: DishName | None = None
    country_id: BodyId | None = None
    category: DishCategory | None = None
    ingredients: Ingredients | None = None
    instructions: Instructions | None = None
    tags: Tags | None = None
    image: ImageUrl | None = None


class DishSummary(BaseModel):
    id: str
    name: str
    country_id: str
    country_name: str
    category: str
    image: str | None
    average_rating: float | None = Field(description="Average of all users' ratings, null if unrated")
    rating_count: int


class IngredientOut(BaseModel):
    name: str
    measure: str


class DishOut(DishSummary):
    tags: list[str]
    ingredients: list[IngredientOut]
    instructions: str
    created_at: str
    youtube: str | None = None
    source: str | None = None
