from sqlalchemy import Enum

from app.core.extensions import db
from app.v1.models.base import BaseModel, TimeMixin
from app.v1.enums import PostStatus


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