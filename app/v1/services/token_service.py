import jwt
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class TokenService:
    def __init__(self, settings):
        self.settings = settings
    
    def generate_verification_token(self, email: str) -> str:
        """
        Create email verification token using JWT.
        """
        payload = {
            "email": email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),  # issued at
            "type": "email_verification",
        }
        return jwt.encode(payload, self.settings.SECRET_KEY, algorithm="HS256")

    def confirm_verification_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms="HS256")
            if payload.get("type") != "email_verification":
                logger.warning("Token type mismatch in verification token.")
                return None

            email = payload.get("email")
            if not email:
                logger.warning("Email not found in token payload.")
                return None

            logger.debug(f"Successfully validated verification token for email: {email}")
            return email
        except jwt.ExpiredSignatureError:
            logger.info("Email verification token has expired.")
            return None
        except jwt.InvalidTokenError:
            logger.info("Invalid email verification token.")
            return None
