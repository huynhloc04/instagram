from sqlalchemy.orm import Session
from werkzeug.exceptions import Conflict, Unauthorized

from app.v1.schemas.user import UserCreate, UserEdit
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

def check_user_edit(data: UserEdit, current_user: User) -> None:
    #   Check username
    if data.username == current_user.username:
        raise Conflict("Username cannot be the same as the current username.")
    username = User.query.filter_by(username=data.username).first()
    if username:
        raise Conflict(f"Username {data.username} already exists. Choose another!")
    #   Check email
    if data.email == current_user.email:
        raise Conflict("Email cannot be the same as the current email.")
    email = User.query.filter_by(email=data.email).first()
    if email:
        raise Conflict(f"Email {data.email} already exists. Choose another!")

