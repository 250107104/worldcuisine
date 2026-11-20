from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

from app.core.constants import AVATARS
from app.schemas.input import PatchBody, RequestBody, TrimmedText


def _check_avatar(v: str) -> str:
    if v not in AVATARS:
        raise ValueError(f"avatar must be one of {AVATARS}")
    return v


Avatar = Annotated[str, AfterValidator(_check_avatar)]


Username = Annotated[TrimmedText, StringConstraints(min_length=2, max_length=24)]
Bio = Annotated[TrimmedText, StringConstraints(max_length=160)]


class UserCreate(RequestBody):
    username: Username = Field(examples=["Maria"])
    bio: Bio = ""
    avatar: Avatar | None = Field(default=None, description=f"One of {AVATARS}; defaults to the first")


class UserUpdate(PatchBody):
    """PATCH body: send only the fields you want to change."""
    username: Username | None = None
    bio: Bio | None = None
    avatar: Avatar | None = None


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
