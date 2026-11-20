from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    detail: str
    code: str


class FieldError(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(ErrorResponse):
    errors: list[FieldError] | None = None


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(description="Number of items matching the filters (before paging)")
    limit: int
    offset: int


class DemoResetOut(BaseModel):
    detail: str
    countries: int
    dishes: int
    users: int
