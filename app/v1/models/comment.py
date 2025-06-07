from app.core.extensions import db
from app.v1.models.base import BaseModel


class Comment(BaseModel):
    __tablename__ = "comments"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    parent_comment_id = db.Column(
        db.Integer, db.ForeignKey("comments.id"), nullable=True
    )
    content = db.Column(db.Text)

    def __repr__(self):
        return f"{self.content}"
