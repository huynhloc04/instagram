from datetime import datetime

from pydantic import BaseModel
from werkzeug.exceptions import NotFound

from app.v1.schemas.user import UserRead
from app.v1.models import User, Post
from app.v1.schemas.base import Pagination
from app.v1.enums import PostStatus


class PostCreate(BaseModel):
    caption: str
    user_id: int
    status: str = PostStatus.public.value


class PostRead(BaseModel):
    id: int
    created_at: datetime
    modified_at: datetime
    caption: str
    image_name: str
    status: str
    deleted: bool
    user: UserRead | None = None

    model_config = {"from_attributes": True}

    # @classmethod
    # def from_post(cls, post: Post, include_user: bool = False):
    #     post_dict = {
    #         "id": post.id,
    #         "created_at": post.created_at,
    #         "modified_at": post.modified_at,
    #         "caption": post.caption,
    #         "image_name": post.image_name,
    #         "status": post.status,
    #         "deleted": post.deleted,
    #     }
    #     if include_user:
    #         user = User.query.get(post.user_id)
    #         if not user:
    #             raise NotFound(f"User with id {post.user_id} not found")
    #         post_dict["user"] = UserRead.model_validate(user)
    #     return cls(**post_dict)


class PostReadList(BaseModel):
    posts: list
    pagination: Pagination


class PostEdit(BaseModel):
    caption: str | None = None
    image_name: str | None = None
    status: str | None = None
