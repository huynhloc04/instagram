from sqlalchemy.orm import Session

from app.v1.models import Follow
from app.v1.schemas.follow import FollowUser


def create_follow_user(data: FollowUser, session: Session) -> None:
    follow = Follow(**data.model_dump())
    session.add(follow)
    session.flush()


def get_list_followers(user_id: int):
    """
    SELECT * FROM users
    JOIN follows ON follows.follower_id=users.id
    WHERE follows.following_id=1
    """
