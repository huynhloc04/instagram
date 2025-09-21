import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template
from werkzeug.security import generate_password_hash

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.v1 import create_app

def send_mail_sync(
    subject: str, 
    context: dict, 
    template_name: str, 
    recipient: str,
    app=None
):
    """
    Send an email with HTML template content synchronously (for testing).
    
    Args:
        subject: Email subject line
        context: Template context variables
        template_name: Name of the email template (without .html extension)
        recipient: Email recipient address
        app: Flask application instance (required for template rendering)
    """
    if app is None:
        raise ValueError("Flask app instance is required for template rendering")
        
    msg = MIMEMultipart()
    msg["From"] = "edwin.huynh@novobi.com"
    msg["To"] = recipient
    msg["Subject"] = subject

    # TODO: Handle idempotency later

    # Use Flask application context for template rendering
    with app.app_context():
        html_text = render_template(f"emails/{template_name}.html", **context)
        msg.attach(MIMEText(html_text, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login("edwin.huynh@novobi.com", "wkir wdex oxam ocpg")
        server.sendmail("edwin.huynh@novobi.com", recipient, msg.as_string())
        

if __name__ == "__main__":
    # Create Flask application instance
    app = create_app()
    
    string_context = "verify-email"
    token = generate_password_hash(string_context)
    activate_url = (
        f"http://localhost:3000/account-verify?token={token}"
    )
    data = {
        "activate_url": activate_url,
        "name": "John Doe",
        "app_name": "Instagram",
    }
    subject = f"Account Verification - Instagram"
    
    # Option 1: Send email synchronously (for testing)
    send_mail_sync(
        subject=subject,
        context=data,
        template_name="account_verification",
        recipient="haiharo04@gmail.com",
        app=app
    )
    
    # Option 2: Send email asynchronously using Celery (recommended for production)
    # from app.v1.email import send_mail
    # send_mail.delay(
    #     subject=subject,
    #     context=data,
    #     template_name="account_verification",
    #     recipient="haiharo04@gmail.com"
    # )