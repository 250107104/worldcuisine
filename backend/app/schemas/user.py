from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, field_validator, model_validator

from app.core.constants import AVATARS


def _check_avatar(v: str) -> str:
    if v not in AVATARS:
        raise ValueError(f"avatar must be one of {AVATARS}")
    return v


Avatar = Annotated[str, AfterValidator(_check_avatar)]


def _check_username(v: str) -> str:
    v = v.strip()
    if len(v) < 2:
        raise ValueError("Username must be at least 2 characters after trimming")
    return v


Username = Annotated[str, Field(min_length=2, max_length=24), AfterValidator(_check_username)]


class UserCreate(BaseModel):
    username: Username = Field(examples=["Maria"])
    bio: str = Field(default="", max_length=160)
    avatar: Avatar | None = Field(default=None, description=f"One of {AVATARS}; defaults to the first")

    @field_validator("bio")
    @classmethod
    def bio_clean(cls, v: str) -> str:
        return v.strip()


class UserUpdate(BaseModel):
    """PATCH body: send only the fields you want to change."""
    username: Username | None = None
    bio: str | None = Field(default=None, max_length=160)
    avatar: Avatar | None = None

    @field_validator("bio")
    @classmethod
    def bio_clean(cls, v):
        return v.strip() if v is not None else v

    @model_validator(mode="after")
    def check(self):
        if not self.model_fields_set:
            raise ValueError("Send at least one field to update")
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"'{name}' cannot be null")
        return self


class UserOut(BaseModel):
    id: str
    username: str
    bio: str
    avatar: str
    created_at: str


class UserStats(BaseModel):
    explored: int
    tried: int
    reviews: int
    favorites: int
    watchlist: int
    countries: int
    rated_count: int
    average_rating: float | None
