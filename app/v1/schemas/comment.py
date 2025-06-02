from datetime import datetime

from pydantic import BaseModel

from app.v1.schemas.base import Pagination


class CommentTree(BaseModel):
    id: int
    created_at: datetime
    modified_at: datetime
    user_id: int
    post_id: int
    content: str
    parent_comment_id: int | None = None

    model_config = {
        "from_attributes": True
    }


class CommentReadList(BaseModel):
    comment_tree: list[CommentTree]
    pagination: Pagination