
import smtplib
from flask import render_template, current_app
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import get_settings
from app.core.celery import celery
from app.core.redis import redis_client


settings = get_settings()


@celery.task(
    bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3}, retry_backoff=True
)
def send_mail(
    self,
    subject: str, 
    context: dict, 
    template_name: str, 
    recipient: str,
    idempotency_key: str
):
    """
    Send an email with given HTML template content and context.
    """
    msg = MIMEMultipart()
    msg["From"] = settings.MAIL_USERNAME
    msg["To"] = recipient
    msg["Subject"] = subject

    # Handle idempotency with Idempotency Key.
    if redis_client.conn.get(idempotency_key):
        current_app.logger.info(f"Email already sent to {recipient} with idempotency key {idempotency_key}.")
        return

    try:
        html_text = render_template(f"{template_name}.html", **context)
        msg.attach(MIMEText(html_text, "html"))

        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_USERNAME, recipient, msg.as_string())
            
        redis_client.conn.set(idempotency_key, "sent", ex=60*60*24)
        current_app.logger.info(f"Email sent successfully to {recipient} with idempotency key {idempotency_key}.")
        
    except Exception as e:
        current_app.logger.error(f"Error while sending email: {e}")
        raise self.retry(exc=e)

