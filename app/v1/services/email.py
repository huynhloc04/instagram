import jwt
from datetime import datetime, timezone, timedelta

from flask import current_app
from werkzeug.security import generate_password_hash

from app.core.config import get_settings
from app.v1.models.user import User
from app.v1.email import send_mail

settings = get_settings()

def generate_verification_token(email: str) -> str:
    """
    Create email verification token using JWT.
    """
    payload = {
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),  # issued at
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def confirm_verification_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
        return payload["email"]
    except jwt.ExpiredSignatureError:
        current_app.logger.info("Email verification token has expired.")
        return None
    except jwt.InvalidTokenError:
        current_app.logger.info("Invalid email verification token.")
        return None

def send_verification_email(user: User):
    """
    Send a verification email to the user.
    """
    token = generate_verification_token(email=user.email)
    activate_url = (
        f"{settings.FRONTEND_HOST}/account-verify?token={token}"
    )
    data = {
        "activate_url": activate_url,
        "name": user.fullname,
        "app_name": settings.APP_NAME,
    }
    subject = f"Account Verification - {settings.APP_NAME}"
    send_mail.delay(
        subject=subject,
        context=data,
        template_name="account_verification",
        recipient=user.email,
    )

def send_account_activation_confirmation_email(user: User):
    """
    Send confirmation email when user activate account successfully.
    """
    data = {
        "login_url": f"{settings.FRONTEND_HOST}/login",
        "app_name": settings.APP_NAME,
        "name": user.fullname,
    }
    subject = f"Welcome - {settings.APP_NAME}"
    send_mail.delay(
        subject=subject,
        context=data,
        template_name="account_verification_confirm",
        recipient=user.email,
    )
