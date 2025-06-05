from pydantic import BaseModel


class FollowUser(BaseModel):
    follower_id: int
    following_id: int
