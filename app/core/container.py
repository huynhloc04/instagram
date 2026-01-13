"""
    Reference: https://python-dependency-injector.ets-labs.org/providers
"""

import redis
from google.cloud import storage
from dependency_injector import containers, providers

from app.core.config import get_settings
from app.core.email import celery_send_mail
from app.core.celery import create_celery
from app.core.redis import RedisClient
from app.core.gcs import GCSService
from app.core.database import Database
from app.v1.repositories import UserRepository
from app.v1.services import UserService, EmailService, TokenService


class Container(containers.DeclarativeContainer):
    # Configurations
    settings = providers.Singleton(get_settings)
    celery_app = providers.Singleton(create_celery, settings)

    # Setup Application Lifecycle - startup: Create DB connections before starting application.
    db = providers.Resource(Database, settings.provided.db_url)

    # Repository Factory (session_factory here is the scoped_session, one scoped_session per Flask app => So Singleton)
    user_repository = providers.Factory(
        UserRepository, session_factory=db.provided.session_factory
    )

    # Token Service
    token_service = providers.Factory(TokenService, settings=settings)

    # Email services
    mail_sender = providers.Object(celery_send_mail)
    email_service = providers.Factory(
        EmailService,
        settings=settings,
        mail_sender=mail_sender,
    )

    # Redis
    redis_connection = providers.Singleton(
        redis.Redis,
        host=settings.provided.REDIS_HOST,
        port=settings.provided.REDIS_PORT,
        db=settings.provided.REDIS_DB,
        decode_responses=True,
    )
    redis_client = providers.Singleton(RedisClient, settings, redis_connection)

    # User Service
    user_service = providers.Factory(
        UserService,
        db=db,
        settings=settings,
        user_repo=user_repository,
        redis_client=redis_client,
        email_service=email_service,
        token_service=token_service,
    )

    # Google Cloud Storage
    gcs_client = providers.Singleton(
        storage.Client, project=settings.provided.GOOGLE_CLOUD_PROJECT
    )
    gcs_bucket = providers.Singleton(
        lambda client, bucket_name: client.bucket(bucket_name),
        client=gcs_client,
        bucket_name=settings.provided.BUCKET_NAME,
    )
    gcs_service = providers.Singleton(
        GCSService, settings=settings, bucket=gcs_bucket
    )
