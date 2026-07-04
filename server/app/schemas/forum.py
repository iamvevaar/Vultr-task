"""
Pydantic schemas for the forum (posts + comments), including a small reusable
pagination wrapper.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageMeta


class AuthorOut(BaseModel):
    """Minimal public info about a user, embedded in posts/comments."""
    id: uuid.UUID
    username: str
    model_config = ConfigDict(from_attributes=True)


# --- Requests ---------------------------------------------------------------

class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=20000)


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
    parent_comment_id: uuid.UUID | None = None  # set to reply to another comment


# --- Responses --------------------------------------------------------------

class PostSummary(BaseModel):
    """A post as it appears in the feed list."""
    id: uuid.UUID
    title: str
    body: str
    author: AuthorOut
    view_count: int
    comment_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CommentOut(BaseModel):
    id: uuid.UUID
    body: str
    author: AuthorOut
    parent_comment_id: uuid.UUID | None
    is_solution: bool
    created_at: datetime
    # Nested replies — this makes CommentOut a self-referential (tree) schema.
    replies: list["CommentOut"] = []
    model_config = ConfigDict(from_attributes=True)


class PostDetail(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    author: AuthorOut
    view_count: int
    comment_count: int
    created_at: datetime
    solution_comment_id: uuid.UUID | None  # derived from the comment flagged is_solution
    comments: list[CommentOut]       # top-level comments, each with nested replies


# Resolve the forward reference in CommentOut.replies.
CommentOut.model_rebuild()


# --- Pagination -------------------------------------------------------------

class PaginatedPosts(BaseModel):
    data: list[PostSummary]
    meta: PageMeta  # imported from schemas.common
