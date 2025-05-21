from sqlalchemy import Enum

from app.core.extensions import db
from app.v1.models.base import BaseModel, TimeMixin
from app.v1.enums import PostStatus
from app.v1.models.user import User
from app.v1.schemas.user import UserRead
from app.v1.models.like import Like


class Post(BaseModel):
    __tablename__ = 'posts'
    
    caption = db.Column(db.Text, nullable=True)
    image_name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(
        Enum(PostStatus, name='post_status'), 
        nullable=False,
        default=PostStatus.DRAFT
    )

    def __repr__(self):
        return f"{self.caption}"

    def to_dict(
        self, current_user: User = None, include_user: bool = False, include_like: bool = False
    ) -> dict:
        post_dict = {
            "id": self.id,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "caption": self.caption,
            "image_name": self.image_name,
            "status": self.status.value,
            "deleted": self.deleted,
        }
        if include_user:
            user = User.query.get(self.user_id)
            if not user:
                raise NotFound(f"User with id {self.user_id} not found")
            post_dict["user"] = UserRead.from_orm(user).dict()
        if include_like:
            post_dict["like_count"] =  Like.query.filter_by(post_id=self.id).count()
            post_dict["liked_by_me"] =  Like.query.filter_by(
                post_id=self.id, user_id=current_user.id
            ).first() is not None if current_user else False
        return post_dict


class PostTag(TimeMixin):
    __tablename__ = 'post_tag'
    
    post_id = db.Column(
        db.Integer, 
        db.ForeignKey('posts.id'), 
        nullable=False, 
        primary_key=True
    )
    tag_id = db.Column(
        db.Integer, 
        db.ForeignKey('tags.id'), 
        nullable=False, 
        primary_key=True
    )