import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, validator
from werkzeug.exceptions import BadRequest


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    fullname: str | None = None
    bio: str | None = None
    profile_picture: str | None = None

    @validator("password")
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise BadRequest("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise BadRequest("Password must include at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise BadRequest("Password must include at least one lowercase letter")
        if not re.search(r"[0-9]", value):
            raise BadRequest("Password must include at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise BadRequest("Password must include at least one special character")
        return value


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    fullname: str | None = None
    bio: str | None = None
    profile_picture: str | None = None
    created_at: datetime
    modified_at: datetime

    model_config = {
        "from_attributes": True
    }   #   Accept input as ORM-object, not just from a dict


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserRead


class UserEdit(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    fullname: str | None = None
    bio: str | None = None