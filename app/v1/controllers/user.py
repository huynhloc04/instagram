from sqlalchemy.orm import Session
from app.v1.schemas.user import UserCreate
from app.v1.models.user import User

def create_user(data: UserCreate, session: Session) -> User:
    user = User(
        username=data.username,
        email=data.email,
        fullname=data.fullname,
        bio=data.bio,
        profile_picture=data.profile_picture,
    )
    user.set_password(data.password)
    session.add(user)
    session.flush()
    return user

