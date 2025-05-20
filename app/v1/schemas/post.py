from datetime import datetime

from pydantic import BaseModel
from werkzeug.exceptions import NotFound

from app.v1.schemas.user import UserRead
from app.v1.models import User, Post
from app.v1.schemas.base import Pagination


class PostCreate(BaseModel):
    caption: str
    image_name: str
    user_id: int
    status: str = "draft"


class PostRead(BaseModel):
    id: int
    created_at: datetime
    modified_at: datetime
    caption: str
    image_name: str
    status: str
    deleted: bool
    user: UserRead | None = None

    model_config = {
        "from_attributes": True
    }

    @classmethod
    def from_post(cls, post: Post, include_user: bool = False):
        post_data = cls.from_orm(post)
        if include_user:
            user = User.query.get(post.user_id)
            if not user:
                raise NotFound(f"User with id {post.user_id} not found")
            post_data.user = UserRead.from_orm(user)
        return post_data


class PostReadList(BaseModel):
    posts: list[PostRead]
    pagination: Pagination


class PostEdit(BaseModel):
    caption: str | None = None
    image_name: str | None = None
    status: str | None = None