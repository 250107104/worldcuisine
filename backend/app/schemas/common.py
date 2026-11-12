from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    detail: str
    code: str


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(description="Number of items matching the filters (before paging)")
    limit: int
    offset: int
