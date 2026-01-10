
import logging
import smtplib
from celery import shared_task
from flask import render_template, current_app
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.v1.models import EmailJob
# from app.v1.enums import ImageCronEnum
# from app.core.gcs import _storage_delete

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True
)
def send_mail(
    self,
    key: int,
    subject: str,
    context: dict,
    template_name: str,
    recipient: str
):
    """
        Send an email with HTML template content and handle idempotency

        Args:
            subject: Email subject line
            context: Template context variables
            template_name: Name of the email template (without .html extension)
            recipient: Email recipient address
    """
    settings = current_app.container.settings()
    db = current_app.container.db()
    job: EmailJob = None
    idempotency_key = f'{template_name}_{key}'

    try:
        with db.session() as session:
            smt = select(EmailJob).where(
                EmailJob.idempotency_key == idempotency_key,
                EmailJob.is_sent == True,
            )
            job = session.execute(smt).scalar_one_or_none()

            if job and job.is_sent:
                return {"status": "already_sent"}

            job = EmailJob(idempotency_key=idempotency_key)
            session.add(job)

    except IntegrityError as e:
        raise e

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.MAIL_USERNAME
        msg["To"] = recipient
        msg["Subject"] = subject
        html_text = render_template(f"{template_name}.html", **context)
        msg.attach(MIMEText(html_text, "html"))

        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_USERNAME, recipient, msg.as_string())

        # Update EmailJob status to succeeded and return result
        with db.session() as session:
            smt = update(EmailJob).where(
                EmailJob.idempotency_key == idempotency_key
            ).values(is_sent=True)
            session.execute(smt)

        logger.info(f"Email sent successfully to {recipient}")
        return {"status": "succeeded"}

    except Exception as e:
        logger.error(f"Error while sending email {template_name}: {e}")
        raise self.retry(exc=e)


# @celery.task(
#     bind=True,
#     autoretry_for=(Exception,),
#     retry_kwargs={'max_retries': 3},
#     retry_backoff=True
# )
# def scheduler_delete_image(app):
#     """
#     Delete all unused image uploaded by users
#     - Delete in Database: ImageCron table.
#     - Delete on Google Cloud Storage.
#     """
#     with app.app_context():

#         with db_session() as session:
#             image_names = (
#                 session.query(ImageCron.image_name)
#                 .filter(ImageCron.status == ImageCronEnum.unused.value)
#                 .all()
#             )

#             # Get IDs or names of successfully deleted images
#             deleted_image_names = []

#             #   Delete on the Google Cloud Storage
#             for image_name in image_names:
#                 gcs_filename = os.path.join(settings.BUCKET_FOLDER, image_name[0])
#                 _storage_delete(gcs_filename)
#                 deleted_image_names.append(image_name[0])

#             #   Delete in Database (Only delete images that have been successfully deleted on GCS)
#             if deleted_image_names:
#                 statement = delete(ImageCron).where(
#                     ImageCron.image_name.in_(deleted_image_names)
#                 )
#                 session.execute(statement)
#                 session.commit()