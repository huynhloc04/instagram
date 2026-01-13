# Reference: https://github.com/jod35/JWT-Auth-for-Flask

import logging

from dependency_injector.wiring import inject, Provide
from flask import Blueprint, request, make_response
from flask_limiter.util import get_remote_address
from flask_jwt_extended import jwt_required, set_refresh_cookies

from app.core.extensions import limiter
from app.core.container import Container
from app.v1.utils import api_response, user_or_ip_key, token_required
from app.v1.schemas.user import (
    UserInput,
    UserRead,
    RegistrationResult,
    UserLogin,
    UserLoginResponse,
)
from app.v1.services import UserService

authRoute = Blueprint("auth", __name__, url_prefix="/auth")
logger = logging.getLogger(__name__)


@authRoute.route("/register", methods=["POST"])
@limiter.limit(
    "100/day",
    key_func=get_remote_address,
    error_message="Too many register attempts. Please try again later.",
)
@inject
def register(user_service: UserService = Provide[Container.user_service]):
    # Preprocess and validate request data
    request_data = request.get_json(silent=True)
    parsed_data = UserInput.model_validate(request_data)

    # Register new user
    result: RegistrationResult = user_service.register(data=parsed_data)

    # Validate output
    registered_user = UserRead.model_validate(result.user)

    return api_response(
        data=registered_user.model_dump(),
        message=result.message,
        status=201,
    )


@authRoute.route("/verify/<token>")
@limiter.limit(
    "100/day",
    key_func=get_remote_address,
    error_message="Too many register attempts. Please try again later.",
)
@inject
def verify_account(
    token: str,
    user_service: UserService = Provide[Container.user_service],
):
    """Verify user's account via sent token."""
    message = user_service.verify_account(token=token)

    return api_response(message=message, status=200)


@authRoute.route("/resend-verify", methods=["POST"])
@limiter.limit(
    "100/hours",
    key_func=get_remote_address,
    error_message="Too many attempts. Please try again later.",
)
@inject
def resend_verify_code(
    user_service: UserService = Provide[Container.user_service]
):
    request_data = request.get_json(silent=True)
    email = request_data.get("email")

    # Resend code
    user_service.resend_code(email=email)

    return api_response(message="Code re-sent.", status=201)


@authRoute.route("/login", methods=["POST"])
@limiter.limit(
    "5/minute",
    key_func=user_or_ip_key,
    error_message="Too many login attempts. Please try again later.",
)
@inject
def login(
    user_service: UserService = Provide[Container.user_service]
):
    """
    Login user with email and password
    """
    json_data = request.get_json()
    validated_data = UserLogin.model_validate(json_data)

    access_token, refresh_token, user = user_service.login(data=validated_data)

    login_user = UserLoginResponse(
        access_token=access_token,
        user=UserRead.model_validate(user),
    )

    # Never trust on client, so create token from server
    response = make_response(
        api_response(
            message="Login successfully.",
            data=login_user.model_dump(),
            status=200,
        )
    )

    # csrf_token = token_hex(16)
    # response.set_cookie(
    #     'refresh_token',
    #     refresh_token,
    #     httponly=True,  # Prevent XSS (Important)
    #     secure=True,    # Only through HTTPS
    #     samesite='Lax',
    #     max_age=int(user_service.settings.JWT_REFRESH_TOKEN_EXPIRES),
    #     path='api/v1/auth/refresh',
    # )
    # response.set_cookie(
    #     'csrf_token',
    #     csrf_token,
    #     secure=True,
    #     samesite="Lax",
    #     max_age=3600,
    # )
    # return response
    
    # Use the built-in function instead of manually as above
    set_refresh_cookies(
        response=response,
        encoded_refresh_token=refresh_token,
        max_age=int(user_service.settings.JWT_REFRESH_TOKEN_EXPIRES)
    )
    return response


@authRoute.route("/refresh", methods=["POST"])
@jwt_required(refresh=True, locations="cookies")   # default is `headers`
@inject
def refresh(
    user_service: UserService = Provide[Container.user_service]
):
    access_token, refresh_token = user_service.refresh()

    response = make_response(
        api_response(
            message="Refresh tokens successfully.",
            data={"access_token": access_token},
            status=200,
        )
    )
    set_refresh_cookies(
        response=response,
        encoded_refresh_token=refresh_token,
        max_age=int(user_service.settings.JWT_REFRESH_TOKEN_EXPIRES)
    )
    return response


@authRoute.route("/verify-password", methods=["POST"])
@token_required()
@inject
def verify_password(
    current_user_id: int,
    user_service: UserService = Provide[Container.user_service]
):
    """
        Verify old password before changing it
    """
    data = request.get_json()
    password = data.get("password")

    user_service.verify_password(
        user_id=current_user_id, old_password=password,
    )

    return api_response(
        message="Password verified successfully.",
        status=201,
    )


@authRoute.route("/change-password", methods=["PUT"])
@token_required()
@inject
def change_password(
    current_user_id: int,
    user_service: UserService = Provide[Container.user_service]
):
    """
        Change user password
    """
    data = request.get_json()
    password = data.get("password")

    user_service.changge_password(
        user_id=current_user_id, new_password=password
    )
    
    return api_response(
        message="Password changed successfully. Logout all devices.",
        status=200,
    )


@authRoute.route("/logout", methods=["POST"])
@jwt_required(verify_type=False)
@inject
def logout(
    user_service: UserService = Provide[Container.user_service]
):
    """
        Logout user - blacklists both access :     and refresh tokens
    """
    user_service.logout()

    return api_response(
        message="Logout successfully.",
        status=200,
    )


@authRoute.route("/logout-all", methods=["POST"])
@token_required()
@inject
def logout_all_devices(
    current_user_id: int,
    user_service: UserService = Provide[Container.user_service]
):
    """
        Logout user from all devices
    """
    user_service.redis_client.logout_all_devices(user_id=current_user_id)

    return api_response(
        message="Logged out from all devices successfully.",
        status=201,
    )
