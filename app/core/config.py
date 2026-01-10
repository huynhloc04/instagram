from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=Path(".env"), case_sensitive=True
    )

    SECRET_KEY: str
    APP_NAME: str
    TEMPLATE_FOLDER: str
    PREFERRED_URL_SCHEME: str
    SERVER_NAME: str

    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_ROOT_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_DATABASE: str

    BUCKET_NAME: str
    BUCKET_FOLDER: str
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_APPLICATION_CREDENTIALS: str

    JWT_ACCESS_TOKEN_EXPIRES: str
    JWT_REFRESH_TOKEN_EXPIRES: str
    JWT_REFRESH_COOKIE_NAME: str
    JWT_COOKIE_CSRF_PROTECT: bool

    RATELIMIT_STORAGE_URL: str
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_USE_TLS: bool = False
    MAIL_USE_SSL: bool = False

    FRONTEND_HOST: str

    CORS_ORIGINS: str
    CORS_METHODS: str
    CORS_HEADERS: str
    CORS_SUPPORTS_CREDENTIALS: bool

    @property
    def db_url(self) -> str:
        """Build MySQL database connection URL"""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )


def get_settings() -> Settings:
    return Settings()
