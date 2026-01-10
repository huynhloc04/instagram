import uuid
import logging
import datetime
from werkzeug.exceptions import (
    Conflict,
    BadRequest,
    NotFound,
    Unauthorized,
)
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt,
)

from app.v1.models.user import User
from app.v1.repositories import UserRepository
from app.v1.schemas.user import UserInput, RegistrationResult
from app.v1.services.token_service import TokenService
from app.v1.services.email_service import EmailService
from app.core.redis import RedisClient

logger = logging.getLogger(__name__)


class UserService:
    """
        A BUSSINES LOGIC should be a SINGLE TRANSACTION.
    """
    def __init__(self,
        db,
        settings,
        user_repo: UserRepository,
        email_service: EmailService,
        token_service: TokenService,
        redis_client: RedisClient
    ):
        self.db = db
        self.settings = settings
        self.redis_client = redis_client
        self.user_repo = user_repo
        self.email_service = email_service
        self.token_service = token_service

    def register(self, data: UserInput) -> RegistrationResult:
        user: User = None

        with self.db.session() as session:
            if self.user_repo.get_by_username(data.username):
                raise Conflict(f"Username {data.username} already exists")
            if self.user_repo.get_by_email(data.email):
                raise Conflict(f"Email {data.email} already exists")

            user = User(**data.model_dump(exclude={"password"}))

            user.set_password(data.password)
            session.add(user)

        # Send verification email
        email_sent = False
        try:
            verified_token = self.token_service.generate_verification_token(email=user.email)
            self.email_service.send_verification_email(user=user, token=verified_token)

            email_sent = True
            logger.info(
                f"Verification email sent to {user.email}"
            )
        except Exception as e:
            logger.error(
                f"Failed to send verification email to {user.email}: {e}",
                exc_info=True
            )

        logger.info(
            f"User registered with username: {user.username} successfully."
        )

        if email_sent:
            message = (
                "User registered successfully. "
                "Please check your email for account verification."
            )
        else:
            message = (
                "User registered successfully. "
                "However, we couldn't send the verification email. "
                "Please contact support or try resending the verification email."
            )

        return RegistrationResult(user=user, message=message)

    def resend_code(self, email: str):
        """Resend verification code to user's email."""
        with self.db.session() as session:  # ← Add context manager
            user = self.user_repo.get_by_email(email)
            if not user:
                raise NotFound(f"User with {email} does not exist. Try again!")

        # Send email with new code
        verified_token = self.token_service.generate_verification_token(email=email)
        self.email_service.send_verification_email(user=user, token=verified_token)

    def verify_account(self, token: str) -> str:
        user: User = None

        email = self.token_service.confirm_verification_token(token=token)
        if not email:
            raise BadRequest("Invalid or expiried verification token.")

        with self.db.session() as session:
            user = self.user_repo.get_by_email(email)
            if not user:
                raise NotFound(f"User with {email} does not exist")
            if user.is_verified:
                raise Conflict("Account is already verified.")

            user.is_verified = True
            user.verified_at = int(datetime.datetime.now().timestamp())

            session.flush()
            session.refresh(user)

        # Send email confirmation of verification
        email_sent = False
        try:
            self.email_service.send_account_activation_confirmation_email(user)
            email_sent = True
            logger.info("An confirmation email is sent to you, please check.")
        except Exception:
            logger.error(f"Fail to send confirmation email to {user.email}", exec=True)

        if email_sent:
            message = (
                "Account verified successfully. "
                "Please check yout email for the account confirmation."
            )
        else:
            message = (
                "We couldn't senf the confirmation email. "
                "Please contact support or try resending the verification email."
            )

        return message

    def login(self, data):
        # Check user existence and password
        with self.db.session() as session:
            user = self.user_repo.get_by_email(email=data.email)
            if not user or not user.check_password(password=data.password):
                raise Unauthorized("Incorrect email or password!")
            if not user.is_verified:
                raise Unauthorized("Please verify your account first!")

        # Add the same extra claim to both access
        # and refresh tokens to simplify revocation (if needed)
        token_jit = str(uuid.uuid4())
        extra_claims = {"jit": token_jit}

        # Create access and refresh token
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=extra_claims,
            expires_delta=datetime.timedelta(
                seconds=int(self.settings.JWT_ACCESS_TOKEN_EXPIRES)
            ),
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=extra_claims,
            expires_delta=datetime.timedelta(
                seconds=int(self.settings.JWT_REFRESH_TOKEN_EXPIRES)
            ),
        )

        logger.info(f"User with email {data.email} login successfully.")

        return access_token, refresh_token, user

    def refresh(self):
        identity = get_jwt_identity()
        old_token_jit = get_jwt().get("jit")

        #   Generate a random JIT and just for both access and refresh token
        new_token_jit = str(uuid.uuid4())
        extra_claims = {"jit": new_token_jit}

        #   Revoke old refresh token
        self.redis_client.add_to_blacklist(
            jit=old_token_jit,
            expires_in=int(self.settings.JWT_REFRESH_TOKEN_EXPIRES),
        )

        # Create new access and refresh tokens
        access_token = create_access_token(
            identity=identity,
            additional_claims=extra_claims,
            expires_delta=datetime.timedelta(
                seconds=int(self.settings.JWT_ACCESS_TOKEN_EXPIRES)
            ),
        )
        refresh_token = create_refresh_token(
            identity=identity,
            additional_claims=extra_claims,
            expires_delta=datetime.timedelta(
                seconds=int(self.settings.JWT_REFRESH_TOKEN_EXPIRES)
            ),
        )
        return access_token, refresh_token

    def verify_password(self, user_id: int, old_password: str):
        with self.db.session() as session:  # ← Add context manager
            user = self.user_repo.get_by_id(id=user_id)
            if not user:
                raise NotFound(f"User {user_id} not found.")
            if not user.check_password(old_password):
                raise Unauthorized("Incorrect password.")

            logger.info("Your password is correct.")

    def changge_password(self, user_id: int, new_password: str):
        with self.db.session() as session:
            user = self.user_repo.get_by_id(id=user_id)
            if not user:
                raise NotFound(f"User {user_id} not found.")

            user.set_password(new_password)

        # Revoke tokens to logout all devices
        self.redis_client.logout_all_devices(user_id=user_id)
        logger.info("Password changed, logged out all devices.")

    def logout(self):
        jwt = get_jwt()
        token_type = jwt["type"]
        token_jit = jwt["jit"]

        #   Blacklist both tokens in the pair
        self.redis_client.add_to_blacklist(
            jit=token_jit,
            expires_in=(
                int(self.settings.JWT_ACCESS_TOKEN_EXPIRES)
                if token_type == "access"
                else int(self.settings.JWT_REFRESH_TOKEN_EXPIRES)
            ),
        )
        logger.info("Logout successfully.")
