from werkzeug.exceptions import NotFound

from app.core.extensions import db
from app.v1.models.base import BaseModel, TimeMixin
from app.v1.enums import PostStatus
from app.v1.models.user import User
from app.v1.models.like import Like
from app.v1.models.comment import Comment
from app.core.database import db_session


class Post(BaseModel):
    __tablename__ = "posts"

    caption = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=PostStatus.draft.value)

    def __repr__(self):
        return f"{self.caption}"

    def to_dict(
        self,
        current_user: User = None,
        include_user: bool = False,
        include_like: bool = False,
        include_comment: bool = False,
    ) -> dict:
        post_dict = {
            "id": self.id,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "caption": self.caption,
            "status": self.status,
            "deleted": self.deleted,
        }
        with db_session() as session:
            image = (
                session.query(ImageCron)
                .join(Post, ImageCron.post_id == self.id)
                .filter(Post.id == self.id)
                .first()
            )
            if not image:
                raise NotFound(f"Cannot find image for post {self.id}")
            post_dict["image_name"] = image.image_name
            if include_user:
                user = session.query(User).where(User.id == self.user_id).first()
                if not user:
                    raise NotFound(f"User with id {self.user_id} not found")
                post_dict["user"] = user.to_dict()
            if include_like:
                like_count = session.query(Like).filter_by(post_id=self.id).count()
                liked_by_me = False
                if current_user:
                    liked_by_me = (
                        session.query(Like)
                        .filter_by(post_id=self.id, user_id=current_user.id)
                        .first()
                        is not None
                    )
                post_dict["like_count"] = like_count
                post_dict["liked_by_me"] = liked_by_me
            if include_comment:
                post_dict["comment_count"] = (
                    session.query(Comment).where(Comment.post_id == self.id).count()
                )
        return post_dict


class PostTag(TimeMixin):
    __tablename__ = "post_tag"

    post_id = db.Column(
        db.Integer, db.ForeignKey("posts.id"), nullable=False, primary_key=True
    )
    tag_id = db.Column(
        db.Integer, db.ForeignKey("tags.id"), nullable=False, primary_key=True
    )


class ImageCron(BaseModel):
    __table_name__ = "image_crons"

    image_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="unused")
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=True)
