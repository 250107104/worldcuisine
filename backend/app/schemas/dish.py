from pydantic import BaseModel, Field, field_validator, model_validator


class Ingredient(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    measure: str = Field(default="", max_length=40)

    @field_validator("name", "measure")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v:
            raise ValueError("Ingredient name cannot be blank")
        return v


def _clean_tags(tags: list[str]) -> list[str]:
    cleaned = [t.strip() for t in tags if t.strip()]
    return list(dict.fromkeys(cleaned))  # drop duplicates, keep order


class DishCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100, examples=["Lasagne"])
    country_id: str = Field(examples=["italy"])
    category: str = Field(min_length=2, max_length=40, examples=["Pasta"])
    ingredients: list[Ingredient] = Field(min_length=1, max_length=40)
    instructions: str = Field(min_length=10, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=10)
    image: str | None = Field(default=None, pattern=r"^https?://\S+$", description="http(s) URL")

    @field_validator("name", "category", "instructions", "country_id")
    @classmethod
    def strip_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Value cannot be blank")
        return v

    @field_validator("country_id")
    @classmethod
    def country_lowercase(cls, v: str) -> str:
        return v.lower()          # ids are lowercase, so "Italy" is accepted as "italy"

    @field_validator("tags")
    @classmethod
    def tags_clean(cls, v):
        return _clean_tags(v)

    @model_validator(mode="after")
    def unique_ingredients(self):
        names = [i.name.lower() for i in self.ingredients]
        if len(names) != len(set(names)):
            raise ValueError("Ingredient names must be unique")
        return self


class DishUpdate(BaseModel):
    """PATCH body: send only the fields you want to change."""
    name: str | None = Field(default=None, min_length=2, max_length=100)
    country_id: str | None = None
    category: str | None = Field(default=None, min_length=2, max_length=40)
    ingredients: list[Ingredient] | None = Field(default=None, min_length=1, max_length=40)
    instructions: str | None = Field(default=None, min_length=10, max_length=5000)
    tags: list[str] | None = Field(default=None, max_length=10)
    image: str | None = Field(default=None, pattern=r"^https?://\S+$")

    @field_validator("name", "category", "instructions", "country_id")
    @classmethod
    def strip_text(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Value cannot be blank")
        return v

    @field_validator("country_id")
    @classmethod
    def country_lowercase(cls, v):
        return v.lower() if v is not None else v

    @field_validator("tags")
    @classmethod
    def tags_clean(cls, v):
        return None if v is None else _clean_tags(v)

    @model_validator(mode="after")
    def check(self):
        if not self.model_fields_set:
            raise ValueError("Send at least one field to update")
        for required in ("name", "country_id", "category", "ingredients", "instructions"):
            if required in self.model_fields_set and getattr(self, required) is None:
                raise ValueError(f"'{required}' cannot be null")
        if self.ingredients:
            names = [i.name.lower() for i in self.ingredients]
            if len(names) != len(set(names)):
                raise ValueError("Ingredient names must be unique")
        return self


class DishSummary(BaseModel):
    id: str
    name: str
    country_id: str
    country_name: str
    category: str
    image: str | None
    average_rating: float | None = Field(description="Average of all users' ratings, null if unrated")
    rating_count: int


class DishOut(DishSummary):
    tags: list[str]
    ingredients: list[Ingredient]
    instructions: str
    created_at: str
