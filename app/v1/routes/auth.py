import uuid
from datetime import timedelta

from flask import Blueprint, request, current_app
from flask_limiter.util import get_remote_address
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
)

from app.core.extensions import limiter
from app.core.database import db_session
from app.core.config import settings
from app.v1.utils import api_response
from app.v1.schemas.user import UserCreate, UserRead, UserLoginResponse
from app.v1.services.user import create_user
from app.v1.services.auth import _check_user_register, _check_user_login
from app.v1.utils import user_or_ip_key
from app.core.redis_client import redis_client
from app.v1.utils import token_required
from app.v1.models.user import User


authRoute = Blueprint("auth", __name__, url_prefix="/auth")


@authRoute.route("/register", methods=["POST"])
@limiter.limit(
    "100/day",
    key_func=get_remote_address,
    error_message="Too many register attempts. Please try again later.",
)
def register():
    # 1. Serialize and validate input JSON with Pydantic
    json_data = request.get_json()
    parsed_data = UserCreate.model_validate(json_data)
    _check_user_register(data=parsed_data)

    #   2. Create user
    with db_session() as session:
        created_user = create_user(data=parsed_data, session=session)
        session.commit()
        session.refresh(created_user)

    #   3. Deserialize User DB model to JSON response, convert from ORM-object to Pydantic object
    registerd_user = UserRead.model_validate(created_user)
    current_app.logger.info(
        f"User registered with username: {created_user.username} successfully."
    )
    return api_response(
        data=registerd_user.model_dump(),  #   Also can be used as registerd_user.json()
        message="User registered successfully.",
        status=201,
    )


@authRoute.route("/login", methods=["POST"])
@limiter.limit(
    "5/minute",
    key_func=user_or_ip_key,
    error_message="Too many login attempts. Please try again later.",
)
def login():
    """
    Login user with username and password
    """
    json_data = request.get_json()
    username = json_data.get("username")
    password = json_data.get("password")

    user = _check_user_login(username=username, password=password)
    #   Generate a random JIT and just for both access and refresh token
    token_jit = str(uuid.uuid4())
    extra_claims = {"jit": token_jit}
    #   Create access_token and refresh_token
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=extra_claims,
        expires_delta=timedelta(seconds=int(settings.JWT_ACCESS_TOKEN_EXPIRES)),
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims=extra_claims,
        expires_delta=timedelta(seconds=int(settings.JWT_REFRESH_TOKEN_EXPIRES)),
    )

    #   Validate response
    login_user = UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserRead.model_validate(user),
    )
    current_app.logger.info(f"User {username} login successfully.")
    return api_response(
        message="Login successfully.",
        data=login_user.model_dump(),
        status=201,
    )


@authRoute.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)  #   Check if refresh token is valid
def refresh():
    """
    Refresh access token
    """
    identity = get_jwt_identity()
    old_token_jit = get_jwt()["jit"]
    #   Generate a random JIT and just for both access and refresh token
    token_jit = str(uuid.uuid4())
    extra_claims = {"jit": token_jit}
    access_token = create_access_token(
        identity=identity,
        additional_claims=extra_claims,
        expires_delta=timedelta(seconds=int(settings.JWT_ACCESS_TOKEN_EXPIRES)),
    )
    refresh_token = create_refresh_token(
        identity=identity,
        additional_claims=extra_claims,
        expires_delta=timedelta(seconds=int(settings.JWT_REFRESH_TOKEN_EXPIRES)),
    )
    #   Revoke old refresh token
    redis_client.add_to_blacklist(
        jit=old_token_jit,
        expires_in=int(settings.JWT_REFRESH_TOKEN_EXPIRES),
    )

    return api_response(
        message="Refresh access token successfully.",
        data={"access_token": access_token, "refresh_token": refresh_token},
        status=201,
    )


@authRoute.route("/logout", methods=["POST"])
@jwt_required(verify_type=False)
def logout():
    """
    Logout user - blacklists both access and refresh tokens
    """
    jwt = get_jwt()
    token_type = jwt["type"]
    token_jit = jwt["jit"]

    #   Blacklist both tokens in the pair
    redis_client.add_to_blacklist(
        jit=token_jit,
        expires_in=(
            int(settings.JWT_ACCESS_TOKEN_EXPIRES)
            if token_type == "access"
            else int(settings.JWT_REFRESH_TOKEN_EXPIRES)
        ),
    )
    current_app.logger.info(f"Logout successfully.")
    return api_response(
        message=f"Logout successfully.",
        status=200,
    )


@authRoute.route("/logout-all", methods=["POST"])
@token_required
def logout_all_devices(current_user: User):
    """
    Logout user from all devices
    """
    redis_client.add_to_logout_all_devices(user_id=current_user.id)
    return api_response(
        message="Logged out from all devices successfully.",
        status=201,
    )
