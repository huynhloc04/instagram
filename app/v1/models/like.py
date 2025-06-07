from app.core.extensions import db
from app.v1.models.base import TimeMixin


class Like(TimeMixin):
    __tablename__ = 'likes'
    
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id'), 
        primary_key=True,
        nullable=False
    )
    post_id = db.Column(
        db.Integer, 
        db.ForeignKey('posts.id'), 
        primary_key=True,
        nullable=False
    )
