import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        case_sensitive=True
    )

    SECRET_KEY: str

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    UPLOAD_FOLDER: str

    @property
    def db_url(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
