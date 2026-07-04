"""
Forum routes (mounted under /api):

  GET   /posts                          list, paginated, sort=latest|trending
  POST  /posts                          create thread   -> emits post_created
  GET   /posts/{id}                     thread + nested comments -> emits post_viewed
  POST  /posts/{id}/comments            add comment     -> emits comment_posted
  PATCH /posts/{id}/solution/{cid}      mark solution (owner only) -> emits solution_marked

Every write action funnels through record_event() — the same idempotent path as
the public /events endpoint — so the forum is just another event producer.
"""

from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import bad_request, forbidden, not_found
from app.models.post import Comment, Post
from app.models.user import User
from app.schemas.forum import (
    AuthorOut,
    CommentCreate,
    CommentOut,
    PageMeta,
    PaginatedPosts,
    PostCreate,
    PostDetail,
    PostSummary,
)
from app.services.event_service import record_event

router = APIRouter(prefix="/posts", tags=["forum"])

# The forum owns these event-type names. The engine never hardcodes them; it only
# sees whatever string arrives in an event.
EVENT_POST_CREATED = "post_created"
EVENT_POST_VIEWED = "post_viewed"
EVENT_COMMENT_POSTED = "comment_posted"
EVENT_SOLUTION_MARKED = "solution_marked"


# --- helpers ----------------------------------------------------------------

def _build_comment_tree(comments: list[Comment]) -> list[CommentOut]:
    """Turn a flat list of comments into a nested tree via parent_comment_id."""
    nodes: dict[int, CommentOut] = {}
    for c in comments:
        nodes[c.id] = CommentOut(
            id=c.id,
            body=c.body,
            author=AuthorOut.model_validate(c.author),
            parent_comment_id=c.parent_comment_id,
            is_solution=c.is_solution,
            created_at=c.created_at,
            replies=[],
        )

    roots: list[CommentOut] = []
    for c in sorted(comments, key=lambda x: x.created_at):
        node = nodes[c.id]
        if c.parent_comment_id and c.parent_comment_id in nodes:
            nodes[c.parent_comment_id].replies.append(node)
        else:
            roots.append(node)
    return roots


def _post_detail(post: Post) -> PostDetail:
    solution_id = next((c.id for c in post.comments if c.is_solution), None)
    return PostDetail(
        id=post.id,
        title=post.title,
        body=post.body,
        author=AuthorOut.model_validate(post.author),
        view_count=post.view_count,
        comment_count=post.comment_count,
        created_at=post.created_at,
        solution_comment_id=solution_id,
        comments=_build_comment_tree(post.comments),
    )


# --- routes -----------------------------------------------------------------

@router.get("", response_model=PaginatedPosts)
def list_posts(
    sort: Literal["latest", "trending"] = "latest",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # Public: guests can browse the feed. (Deliberate deviation, see PLAN.)
    total = db.scalar(select(func.count()).select_from(Post)) or 0

    if sort == "trending":
        # Engagement score: comments count 3x as much as views. Tie-break by
        # recency. (A documented simplification; time-decay could be added.)
        order_by = (Post.view_count + Post.comment_count * 3).desc()
    else:
        order_by = Post.created_at.desc()

    posts = db.scalars(
        select(Post).order_by(order_by, Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    pages = (total + limit - 1) // limit  # ceil division
    return PaginatedPosts(
        data=[PostSummary.model_validate(p) for p in posts],
        meta=PageMeta(page=page, limit=limit, total=total, pages=pages),
    )


@router.post("", response_model=PostDetail, status_code=status.HTTP_201_CREATED)
def create_post(
    body: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = Post(author_id=current_user.id, title=body.title, body=body.body)
    db.add(post)
    db.commit()
    db.refresh(post)

    # Emit the event AFTER the post exists, keyed by post id so it's idempotent.
    record_event(
        db,
        event_id=f"{EVENT_POST_CREATED}:{post.id}",
        user_id=current_user.id,
        event_type=EVENT_POST_CREATED,
        payload={"post_id": post.id},
    )
    return _post_detail(post)


@router.get("/{post_id}", response_model=PostDetail)
def get_post(
    post_id: int,
    current_user: User | None = Depends(get_optional_user),  # public: guests allowed
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if post is None:
        raise not_found("Post not found")

    # Only logged-in users generate a view event. A view is counted at most once
    # per user per day (in APP_TZ); the event_id encodes that rule so refreshes
    # don't inflate view challenges. Guests just read — no event, no counter bump.
    if current_user is not None:
        today = datetime.now(ZoneInfo(settings.app_tz)).date().isoformat()
        _, created = record_event(
            db,
            event_id=f"{EVENT_POST_VIEWED}:{current_user.id}:{post.id}:{today}",
            user_id=current_user.id,
            event_type=EVENT_POST_VIEWED,
            payload={"post_id": post.id},
        )
        if created:
            post.view_count += 1
            db.commit()
            db.refresh(post)

    return _post_detail(post)


@router.post("/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int,
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if post is None:
        raise not_found("Post not found")

    if body.parent_comment_id is not None:
        parent = db.get(Comment, body.parent_comment_id)
        if parent is None or parent.post_id != post_id:
            raise bad_request("parent_comment_id does not belong to this post")

    comment = Comment(
        post_id=post_id,
        author_id=current_user.id,
        parent_comment_id=body.parent_comment_id,
        body=body.body,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    post.comment_count += 1
    db.commit()

    record_event(
        db,
        event_id=f"{EVENT_COMMENT_POSTED}:{comment.id}",
        user_id=current_user.id,
        event_type=EVENT_COMMENT_POSTED,
        payload={"post_id": post_id, "comment_id": comment.id},
    )

    return CommentOut(
        id=comment.id,
        body=comment.body,
        author=AuthorOut.model_validate(comment.author),
        parent_comment_id=comment.parent_comment_id,
        is_solution=comment.is_solution,
        created_at=comment.created_at,
        replies=[],
    )


@router.patch("/{post_id}/solution/{comment_id}", response_model=PostDetail)
def mark_solution(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if post is None:
        raise not_found("Post not found")

    # Only the post owner may mark a solution -> 403 for anyone else.
    if post.author_id != current_user.id:
        raise forbidden("Only the post owner can mark a solution")

    comment = db.get(Comment, comment_id)
    if comment is None or comment.post_id != post_id:
        raise not_found("Comment not found on this post")

    # Enforce at most one solution per post: clear any previous one.
    for c in post.comments:
        if c.is_solution and c.id != comment.id:
            c.is_solution = False
    comment.is_solution = True
    db.commit()

    # Credit the COMMENT AUTHOR — they wrote the accepted answer.
    record_event(
        db,
        event_id=f"{EVENT_SOLUTION_MARKED}:{post_id}:{comment_id}",
        user_id=comment.author_id,
        event_type=EVENT_SOLUTION_MARKED,
        payload={"post_id": post_id, "comment_id": comment_id, "marked_by": current_user.id},
    )

    db.refresh(post)
    return _post_detail(post)
