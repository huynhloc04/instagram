from app.v1.models.user import User


class EmailService:
    def __init__(self, settings, mail_sender):
        self.settings = settings
        self.mail_sender = mail_sender

    def send_verification_email(self, user: User, token: str):
        """
        Send a verification email to the user.
        """
        data = {
            "activate_url": f"{self.settings.FRONTEND_HOST}/account-verify?token={token}",
            "name": user.fullname,
            "app_name": self.settings.APP_NAME,
        }
        subject = f"Account Verification - {self.settings.APP_NAME}"
        self.mail_sender(
            key=user.id,
            subject=subject,
            context=data,
            template_name="account_verification",
            recipient=user.email,
        )


    def send_account_activation_confirmation_email(self, user: User):
        """
        Send confirmation email when user activate account successfully.
        """
        data = {
            "login_url": f"{self.settings.FRONTEND_HOST}/login",
            "app_name": self.settings.APP_NAME,
            "name": user.fullname,
        }
        subject = f"Welcome - {self.settings.APP_NAME}"
        self.mail_sender(
            key=user.id,
            subject=subject,
            context=data,
            template_name="account_verification_confirm",
            recipient=user.email,
        )
