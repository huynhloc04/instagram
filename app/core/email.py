import logging

from app.v1.tasks import send_mail

logger = logging.getLogger(__name__)


def celery_send_mail(**kwargs):
    send_mail.delay(**kwargs)


