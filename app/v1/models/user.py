from sqlalchemy import String, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash

from app.v1.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    fullname: Mapped[str] = mapped_column(String(100), nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    verified_at: Mapped[int] = mapped_column(Integer, nullable=True)
    profile_picture: Mapped[str] = mapped_column(
        String(256),
        default="default.jpg",
        nullable=False
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # def to_dict(self, viewer=None, excludes: list[str] = None) -> dict:
    #     user_dict = {
    #         "id": self.id,
    #         "username": self.username,
    #         "email": self.email,
    #         "fullname": self.fullname,
    #         "bio": self.bio,
    #         "profile_picture": self.profile_picture,
    #         "created_at": self.created_at,
    #         "modified_at": self.modified_at,
    #     }
    #     if viewer:
    #         # user_dict["posts"] = None
    #         user_dict["num_to_follow"] = Follow.query.filter_by(
    #             follower_id=self.id
    #         ).count()
    #         user_dict["num_followed"] = Follow.query.filter_by(
    #             following_id=self.id
    #         ).count()
    #         user_dict["is_following"] = (
    #             Follow.query.filter_by(
    #                 follower_id=viewer.id, following_id=self.id
    #             ).first()
    #             is not None
    #         )  #   or None
    #     if excludes:
    #         for exclude in excludes:
    #             user_dict.pop(exclude, None)
    #     return user_dict

