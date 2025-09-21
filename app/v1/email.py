
import smtplib
from flask import render_template, current_app
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import get_settings
from app.core.celery import celery


settings = get_settings()

@celery.task(
    bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3}, retry_backoff=True
)
def send_mail(
    self,
    subject: str, 
    context: dict, 
    template_name: str, 
    recipient: str
):
    """
    Send an email with HTML template content.
    
    Args:
        subject: Email subject line
        context: Template context variables
        template_name: Name of the email template (without .html extension)
        recipient: Email recipient address
        
    Note: This task automatically runs within Flask app context when 
          Celery is properly configured with the app factory.
    """
    msg = MIMEMultipart()
    msg["From"] = settings.MAIL_USERNAME
    msg["To"] = recipient
    msg["Subject"] = subject

    # TODO: Handle idempotency later => Enforced via DB or deduplication key.

    try:
        html_text = render_template(f"{template_name}.html", **context)
        msg.attach(MIMEText(html_text, "html"))

        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_USERNAME, recipient, msg.as_string())
            
        current_app.logger.info(f"Email sent successfully to {recipient}")
        
    except Exception as e:
        current_app.logger.error(f"Error while sending email: {e}")
        raise self.retry(exc=e)
