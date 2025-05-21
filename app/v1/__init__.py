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
from app.logs.config import setup_logging
from app.v1.storage import bucket
from flask import redirect

load_dotenv()

rootRoute = Blueprint("root", __name__,  url_prefix='/api/v1')

@rootRoute.route("/<string:image_name>", methods=['GET'])
def serve_image(image_name: str):
    try:
        gcs_filename = os.path.join(settings.POST_BUCKET_FOLDER, image_name)
        blob = bucket.blob(gcs_filename)
        if not blob.exists():
            abort(404, description="File not found.")

        return blob.public_url
    except Exception as error:
        raise IndentationError(str(error))


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # app.config.from_mapping(settings.dict())

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