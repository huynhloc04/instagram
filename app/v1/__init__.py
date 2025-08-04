from flask import Flask, Blueprint, jsonify
from dotenv import load_dotenv
from prometheus_client import make_wsgi_app, REGISTRY
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.extensions import limiter
from app.core.handlers import register_error_handlers
from app.core.extensions import register_extensions, jwt
from app.v1.routes.auth import authRoute
from app.v1.routes.user import userRoute
from app.v1.routes.post import postRoute
from app.logs.config import init_logging
from app.v1.utils import register_dependencies
from app.v1.schedulers import scheduler_delete_image
from app.core.redis_client import redis_client


load_dotenv()
scheduler = BackgroundScheduler()
rootRoute = Blueprint("root", __name__, url_prefix="/api/v1")


@rootRoute.route("/health", methods=["GET"])
@limiter.exempt
def index():
    return jsonify({"status": "healthy"}), 200


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

    # Setup JWT
    @jwt.token_in_blocklist_loader
    def token_in_blocklist_callback(jwt_header, jwt_data):
        jit_token = jwt_data["jit"]
        return redis_client.is_blacklisted(jit_token)

    # @jwt.user_lookup_loader
    # def user_lookup_callback(jwt_header, jwt_data):
    #     identity = jwt_data["sub"]
    #     with db_session() as session:
    #         user = session.query(User).filter(User.id == identity).scalar()
    #         if user and user.last_logout_all_devices:
    #             # Check if token was issued before the last logout all devices
    #             token_issued_at = jwt_data.get("iat")
    #             if token_issued_at and user.last_logout_all_devices.timestamp() > token_issued_at:
    #                 return None  # Token is invalid
    #     return user

    register_dependencies(app)
    app.wsgi_app = DispatcherMiddleware(
        app.wsgi_app, {"/metrics": make_wsgi_app(REGISTRY)}
    )

    #   Register background schedulers
    scheduler.add_job(scheduler_delete_image, "interval", days=1, kwargs={"app": app})
    scheduler.start()

    return app
