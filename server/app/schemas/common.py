"""Shared schema pieces used across endpoints."""

from pydantic import BaseModel


class PageMeta(BaseModel):
    """Pagination metadata returned alongside any paginated list."""
    page: int
    limit: int
    total: int
    pages: int
