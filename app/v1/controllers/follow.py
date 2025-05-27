from werkzeug.exceptions import BadRequest, NotFound, Conflict
from sqlalchemy.orm import Session

from app.v1.models import User, Follow
from app.v1.schemas.follow import FollowUser


def create_follow_user(data: FollowUser, session: Session) -> None:
    follow = Follow(**data.dict())
    session.add(follow)
    session.flush()

def get_list_followers(user_id: int):
    """
        SELECT * FROM users
        JOIN follows ON follows.follower_id=users.id
        WHERE follows.following_id=1
    """