import os

from flask import Flask, Blueprint
from dotenv import load_dotenv
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from app.core.config import settings
from app.v1.controllers.auth import auth_bp
from app.v1.controllers.user import user_bp

load_dotenv()

root_bp = Blueprint("root", __name__,  url_prefix='/api/v1')

# Initialize extensions
jwt = JWTManager()
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    Swagger(app)

    app.config["SECRET_KEY"] = settings.secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    #   Initialize Flask extensions
    jwt.init_app(app)
    db.init_app(app)

    #   Register blueprints
    root_bp.register_blueprint(auth_bp)
    root_bp.register_blueprint(user_bp)
    app.register_blueprint(root_bp)

    return app