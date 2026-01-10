from flask import Flask
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

from app.core.config import get_settings

settings = get_settings()


jwt = JWTManager()
swagger = Swagger()
cors = CORS()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.RATELIMIT_STORAGE_URL
    # default_limits=["200/day", "50/hour", "10/minute"],
)

def register_extensions(settings, app: Flask):
    jwt.init_app(app)
    swagger.init_app(app)
    limiter.init_app(app)

    cors.init_app(
        app,
        origins=(
            settings.CORS_ORIGINS.split(",")
            if settings.CORS_ORIGINS != "*"
            else "*"
        ),
        methods=settings.CORS_METHODS.split(","),
        allow_headers=settings.CORS_HEADERS.split(","),
        supports_credentials=settings.CORS_SUPPORTS_CREDENTIALS    # Allow to send cookie
    )
