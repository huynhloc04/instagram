from app.core.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app.v1.models.base import BaseModel
from app.v1.models.follow import Follow

class User(BaseModel):
    __tablename__ = 'users'
    
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(255), default='default.jpg')

    def __repr__(self):
        return f"User {self.username}"
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, viewer=None, excludes: list[str] = None) -> dict:
        user_dict = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "fullname": self.fullname,
            "bio": self.bio,
            "profile_picture": self.profile_picture,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }
        if viewer:
            # user_dict["posts"] = None
            user_dict["num_to_follow"] = Follow.query.filter_by(follower_id=self.id).count()
            user_dict["num_followed"] = Follow.query.filter_by(following_id=self.id).count()
            user_dict["is_following"] = Follow.query.filter_by(
                follower_id=viewer.id, following_id=self.id
            ).first() is not None   #   or None
        if excludes:
            for exclude in excludes:
                user_dict.pop(exclude, None)
        return user_dict
