from app.core.extensions import db
from app.v1.models.base import TimeMixin


class Follow(TimeMixin):
    __tablename__ = "follows"

    follower_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), primary_key=True, nullable=False
    )  #  Indicating the user who is doing the following.
    following_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), primary_key=True, nullable=False
    )  #  Indicating the user being followed.

    def __repr__(self):
        return f"{self.following_id}"
