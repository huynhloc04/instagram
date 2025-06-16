import os

from flask import Flask, Blueprint
from dotenv import load_dotenv
from werkzeug.exceptions import NotFound
from prometheus_client import make_wsgi_app, REGISTRY
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.handlers import register_error_handlers
from app.core.extensions import register_extensions
from app.v1.routes.auth import authRoute
from app.v1.routes.user import userRoute
from app.v1.routes.post import postRoute
from app.logs.config import init_logging
from app.v1.storage import bucket
from app.v1.utils import api_response, register_dependencies
from app.v1.schedulers import scheduler_delete_image


load_dotenv()
scheduler = BackgroundScheduler()

rootRoute = Blueprint("root", __name__, url_prefix="/api/v1")


@rootRoute.route("/public", methods=["GET"])
def index():
    return api_response(message="This is a public route.")


@rootRoute.route("/<string:image_name>", methods=["GET"])
def serve_image(image_name: str):
    try:
        gcs_filename = os.path.join(settings.POST_BUCKET_FOLDER, image_name)
        blob = bucket.blob(gcs_filename)
        if not blob.exists():
            NotFound(404, description="File not found.")

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
    init_logging(app)

    register_dependencies(app)
    app.wsgi_app = DispatcherMiddleware(
        app.wsgi_app, {"/metrics": make_wsgi_app(REGISTRY)}
    )

    #   Register background schedulers
    scheduler.add_job(scheduler_delete_image, "interval", days=1, kwargs={"app": app})
    scheduler.start()

    return app
