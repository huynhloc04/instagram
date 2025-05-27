from werkzeug.exceptions import Conflict, Unauthorized

from app.v1.schemas.user import UserCreate
from app.v1.models.user import User


def check_user_register(data: UserCreate) -> None:
    #   Check username
    username = User.query.filter_by(username=data.username).first()
    if username:
        raise Conflict(f"Username {data.username} already exists")
    #   Check email
    email = User.query.filter_by(email=data.email).first()
    if email:
        raise Conflict(f"Email {data.email} already exists")

def check_user_login(username: str, password: str) -> User:
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        raise Unauthorized(f"Incorrect username or password!")
    return user