import re
from datetime import datetime
from dataclasses import dataclass

from pydantic import BaseModel, EmailStr, field_validator

# from app.v1.models.follow import Follow
from app.v1.models.user import User
from app.v1.schemas.base import Pagination


class UserInput(BaseModel):
    username: str
    email: EmailStr
    password: str
    fullname: str | None = None
    bio: str | None = None
    profile_picture: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not value or len(value.strip()) == 0:
            raise ValueError("Username is required")
        if len(value) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(value) > 20:
            raise ValueError("Username must not exceed 20 characters")
        # Allow only alphanumeric, underscore, and hyphen
        if not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise ValueError(
                "Username can only contain letters, numbers, "
                "underscores, and hyphens"
            )
        # Must start with letter or number
        if not re.match(r"^[a-zA-Z0-9]", value):
            raise ValueError(
                "Username must start with a letter or number"
            )

        return value.lower()  # Normalize to lowercase

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must include at least one uppercase letter"
            )
        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must include at least one lowercase letter"
            )
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must include at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError(
                "Password must include at least one special character"
            )
        return value


class UserRead(BaseModel):
    """
    Public user schema - returned in registration and login responses.
    Excludes sensitive information like email.
    """
    id: int
    username: str
    fullname: str | None = None
    bio: str | None = None
    profile_picture: str | None = None
    is_verified: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class UserPrivate(BaseModel):
    """
    Private user schema - includes sensitive information.
    Only returned to the authenticated user viewing their own profile.
    """
    id: int
    username: str
    email: EmailStr
    fullname: str | None = None
    bio: str | None = None
    profile_picture: str | None = None
    is_verified: bool
    created_at: datetime
    modified_at: datetime

    model_config = {
        "from_attributes": True
    }


@dataclass
class RegistrationResult:
    user: User
    message: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    user: UserRead


class UserEdit(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    fullname: str | None = None
    bio: str | None = None


class UserReadList(BaseModel):
    users: list[UserRead]
    pagination: Pagination
