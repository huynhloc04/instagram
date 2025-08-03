from datetime import timedelta

from flask import Blueprint, request, current_app
from flask_limiter.util import get_remote_address
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
    decode_token,
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
from werkzeug.exceptions import InternalServerError


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
    #   Create access_token and refresh_token
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(seconds=int(settings.JWT_ACCESS_TOKEN_EXPIRES)),
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        expires_delta=timedelta(seconds=int(settings.JWT_REFRESH_TOKEN_EXPIRES)),
    )

    # Extract JTIs and store token pair
    try:
        access_jti = decode_token(access_token)["jti"]
        refresh_jti = decode_token(refresh_token)["jti"]

        # Store token pair relationship
        redis_client.store_token_pair(
            access_jti=access_jti,
            refresh_jti=refresh_jti,
            expires_in=int(settings.JWT_REFRESH_TOKEN_EXPIRES),
        )
    except Exception as e:
        current_app.logger.error(f"Error storing token pair during login: {e}")

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
    access_token = create_access_token(
        identity=identity,
        expires_delta=timedelta(seconds=int(settings.JWT_ACCESS_TOKEN_EXPIRES)),
    )
    refresh_token = create_refresh_token(
        identity=identity,
        expires_delta=timedelta(seconds=int(settings.JWT_REFRESH_TOKEN_EXPIRES)),
    )

    # Extract new JTIs and manage token pairs
    try:
        old_refresh_jti = get_jwt()["jti"]
        old_access_jti = redis_client.get_paired_token(old_refresh_jti, "refresh")
        new_access_jti = decode_token(access_token)["jti"]
        new_refresh_jti = decode_token(refresh_token)["jti"]
        # Remove old token pair mapping
        if old_access_jti:
            redis_client.remove_token_pair(old_access_jti, old_refresh_jti)

        # Store new token pair relationship
        redis_client.store_token_pair(
            access_jti=new_access_jti,
            refresh_jti=new_refresh_jti,
            expires_in=int(settings.JWT_REFRESH_TOKEN_EXPIRES),
        )
    except Exception as e:
        current_app.logger.error(f"Error managing token pairs during refresh: {e}")

    current_app.logger.info(f"Refresh access token successfully.")

    #   Revoke old refresh token
    redis_client.add_to_blacklist(
        old_refresh_jti, expires_in=int(settings.JWT_REFRESH_TOKEN_EXPIRES)
    )
    # Also blacklist old access token if it exists
    if old_access_jti:
        redis_client.add_to_blacklist(
            old_access_jti, expires_in=int(settings.JWT_ACCESS_TOKEN_EXPIRES)
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

    #   Blacklist both tokens in the pair
    redis_client.blacklist_token_pair(
        jti=jwt["jti"],
        token_type=jwt["type"],
        expires_in=int(settings.JWT_REFRESH_TOKEN_EXPIRES),
    )
    current_app.logger.info(
        f"Logout successfully. Both access and refresh tokens revoked."
    )
    return api_response(
        message="Logout successfully. Both access and refresh tokens revoked.",
        status=200,
    )


# @authRoute.route("/logout-all-devices", methods=["POST"])
# @token_required
# def logout_all_devices(current_user: User):
#     """
#     Logout user from all devices
#     """
#     with db_session() as session:
#         # Get the current user from session to ensure we're working with the latest data
#         user = session.query(User).filter(User.id == current_user.id).first()
#         if user:
#             user.logout_all_devices()
#             session.commit()
#             current_app.logger.info(f"User {user.username} logged out from all devices successfully.")
#             return api_response(
#                 message="Logged out from all devices successfully.",
#                 status=200,
#             )
#         else:
#             return api_response(
#                 message="User not found.",
#                 status=404,
#             )
