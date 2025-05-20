import os

from flask import Flask, Blueprint, send_file
from dotenv import load_dotenv
from flasgger import Swagger
from werkzeug.exceptions import NotFound
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from app.core.config import settings
from app.core.handlers import register_error_handlers
from app.core.extensions import register_extensions
from app.v1.routes.auth import authRoute
from app.v1.routes.user import userRoute
from app.v1.routes.post import postRoute
from app.core.log_config import setup_logging

load_dotenv()

rootRoute = Blueprint("root", __name__,  url_prefix='/api/v1')

@rootRoute.route("/<string:image_name>", methods=['GET'])
def serve_image(image_name: str):
    image_path = os.path.join(
        os.getcwd(), settings.UPLOAD_FOLDER, image_name
    )
    if not os.path.exists(image_path):
      raise NotFound("File not found.")
    return send_file(image_path)


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    #   Register extensions
    register_extensions(app)

    #   Register blueprints
    rootRoute.register_blueprint(authRoute)
    rootRoute.register_blueprint(userRoute)
    rootRoute.register_blueprint(postRoute)
    app.register_blueprint(rootRoute)

    #   Register error handlers
    register_error_handlers(app)

    #   Setup logging
    setup_logging(app)

    return app