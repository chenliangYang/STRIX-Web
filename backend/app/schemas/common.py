"""Common schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseBase(BaseModel):
    """Base response."""

    code: int = 0
    message: str = "ok"


class ResponseData(ResponseBase, Generic[T]):
    """Response with data."""

    data: T | None = None


class PaginatedData(BaseModel):
    """Paginated data."""

    items: list[Any] = []
    total: int = 0
    page: int = 1
    pageSize: int = 20


class PaginatedResponse(ResponseBase):
    """Paginated response."""

    data: PaginatedData = PaginatedData()
