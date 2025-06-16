from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flasgger import Swagger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.core.config import settings

db = SQLAlchemy()
jwt = JWTManager()
swagger = Swagger()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.RATELIMIT_STORAGE_URL,
    default_limits=["200/day", "50/hour", "10/minute"],
)


def register_extensions(app: Flask):
    jwt.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    swagger.init_app(app)
    limiter.init_app(app)
