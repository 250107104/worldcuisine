from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field, StringConstraints, model_validator

from app.core.constants import AVATARS
from app.schemas.input import PatchBody, RequestBody, TrimmedText


def _check_avatar(v: str) -> str:
    if v not in AVATARS:
        raise ValueError(f"avatar must be one of {AVATARS}")
    return v


def _normalize_email(value: EmailStr) -> str:
    return str(value).strip().lower()


Avatar = Annotated[str, AfterValidator(_check_avatar)]
Email = Annotated[EmailStr, AfterValidator(_normalize_email)]
Username = Annotated[TrimmedText, StringConstraints(min_length=2, max_length=24)]
Bio = Annotated[TrimmedText, StringConstraints(max_length=160)]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class UserCreate(RequestBody):
    username: Username = Field(examples=["Maria"])
    email: Email | None = None
    password: Password | None = Field(default=None, exclude=True, repr=False)
    bio: Bio = ""
    avatar: Avatar | None = Field(default=None, description=f"One of {AVATARS}; defaults to the first")

    @model_validator(mode="after")
    def credentials_are_paired(self):
        if (self.email is None) != (self.password is None):
            raise ValueError("email and password must be provided together")
        return self


class RegistrationCreate(RequestBody):
    """Validated input for creating a password-based account."""
    username: Username = Field(examples=["Maria"])
    email: Email
    password: Password = Field(repr=False)
    bio: Bio = ""
    avatar: Avatar | None = Field(default=None, description=f"One of {AVATARS}; defaults to the first")


class UserUpdate(PatchBody):
    """PATCH body: send only the fields you want to change."""
    username: Username | None = None
    email: Email | None = None
    password: Password | None = Field(default=None, exclude=True, repr=False)
    bio: Bio | None = None
    avatar: Avatar | None = None

    @model_validator(mode="after")
    def credentials_are_paired(self):
        if "password" in self.model_fields_set and "email" not in self.model_fields_set:
            raise ValueError("email must be provided when changing the password")
        if "email" in self.model_fields_set and self.email is None:
            if "password" in self.model_fields_set and self.password is not None:
                raise ValueError("email cannot be cleared while setting a password")
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
