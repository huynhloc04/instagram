from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=Path(".env"), case_sensitive=True)

    SECRET_KEY: str

    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_ROOT_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_DATABASE: str

    BUCKET_NAME: str
    BUCKET_FOLDER: str

    JWT_ACCESS_TOKEN_EXPIRES: str
    JWT_REFRESH_TOKEN_EXPIRES: str

    GCS_KEY: str | None = None

    RATELIMIT_STORAGE_URL: str

    @property
    def db_url(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"


settings = Settings()
