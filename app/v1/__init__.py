from flask import Flask, Blueprint
from dotenv import load_dotenv
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from app.core.config import settings
from app.core.handlers import register_error_handlers
from app.core.extensions import register_extensions
from app.v1.routes.auth import auth_bp
from app.v1.routes.user import user_bp

load_dotenv()

root_bp = Blueprint("root", __name__,  url_prefix='/api/v1')


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    #   Register extensions
    register_extensions(app)

    #   Register blueprints
    root_bp.register_blueprint(auth_bp)
    root_bp.register_blueprint(user_bp)
    app.register_blueprint(root_bp)

    #   Register error handlers
    register_error_handlers(app)

    return app