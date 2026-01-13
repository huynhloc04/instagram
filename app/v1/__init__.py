import logging
from flask import Flask, Blueprint, jsonify, request
# from prometheus_client import make_wsgi_app, REGISTRY
# from werkzeug.middleware.dispatcher import DispatcherMiddleware
# from apscheduler.schedulers.background import BackgroundScheduler

from app.core.extensions import limiter
from app.core.handlers import register_error_handlers
from app.core.extensions import register_extensions, jwt
from app.core.container import Container
from app.v1.routes.auth import authRoute
# from app.v1.routes.user import userRoute
# from app.v1.routes.post import postRoute
from app.core.logging import configure_logging
from werkzeug.exceptions import Forbidden

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    # 1. Create DI container
    container = Container()

    # 2. Resolve settings ONCE via container
    settings = container.settings()

    # 3. Configure logging early (infrastructure)
    configure_logging(
        log_level="DEBUG",
        log_file="app/logs/app.log",
    )

    # 4. Create Flask app
    app = Flask(
        __name__,
        template_folder=settings.TEMPLATE_FOLDER,
        static_url_path="/static",
    )

    # 5. Attach container to app (entry-point only)
    app.container = container

    # 6. Flask config (extensions only)
    app.config.update(
        SECRET_KEY=settings.SECRET_KEY,
        SQLALCHEMY_DATABASE_URI=settings.db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PREFERRED_URL_SCHEME=settings.PREFERRED_URL_SCHEME,
        SERVER_NAME=settings.SERVER_NAME,
        JWT_REFRESH_COOKIE_NAME=settings.JWT_REFRESH_COOKIE_NAME,
        JWT_COOKIE_CSRF_PROTECT=settings.JWT_COOKIE_CSRF_PROTECT,
    )

    # 7. Register Flask extensions
    register_extensions(settings, app)

    # 8. Create root blueprint
    # Must be inside create_app to avoid re-registration issues
    rootRoute = Blueprint("root", __name__, url_prefix="/api/v1")

    # Health check endpoint
    @rootRoute.route("/health", methods=["GET"])
    @limiter.exempt
    def index():
        return jsonify({"status": "healthy"}), 200

    # 9. Register sub-blueprints to root
    rootRoute.register_blueprint(authRoute)
    # rootRoute.register_blueprint(userRoute)
    # rootRoute.register_blueprint(postRoute)

    # 10. Register root blueprint to app
    app.register_blueprint(rootRoute)

    # 11. Register error handlers
    register_error_handlers(app)

    # 12. JWT blocklist callback (resolve redis via container)
    redis_client = container.redis_client()

    @jwt.token_in_blocklist_loader
    def token_in_blocklist_callback(jwt_header, jwt_data):
        jit = jwt_data["jit"]
        identity = jwt_data["sub"]
        iat = jwt_data["iat"]

        return (
            redis_client.is_blacklisted(jit)
            or redis_client.is_logout_all_devices(identity, iat)
        )

    # 13. Wire container into routes (DI)
    container.wire(
        modules=[
            "app.v1.routes.auth",
            # "app.v1.routes.user",
            # "app.v1.routes.post",
        ]
    )

    # 14. Prometheus metrics
    # app.wsgi_app = DispatcherMiddleware(
    #     app.wsgi_app,
    #     {"/metrics": make_wsgi_app(REGISTRY)},
    # )

    @app.before_request
    def validate_csrf():
        """
            This is just a demo to study since flask_jwt_extended has already handled this
        """
        # Only check methods that change data
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return

        # Only check with register API
        if request.path != "/refresh":
            return

        csrf_cookie_token = request.cookies.get("csrf_token")
        csrf_header_token = request.headers.get("X-CSRF-Token")     # Similarly when saving on Server since that hacker's web cannot read to our web to get info (by CORS policy) 

        if (
            not csrf_cookie_token or
            not csrf_header_token or
            csrf_header_token != csrf_cookie_token
        ):
            logger.warning(f"CSRF failure from IP: {request.remote_addr}")
            raise Forbidden("CSRF validation failed.")

    @app.teardown_appcontext
    def shutdown_resources(exception=None):
        # This calls Database.shutdown() (disposing the pool)
        container.shutdown_resources()

    # 15. Optional: Background scheduler (DI-aware)
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(
    #     lambda: some_job(container),
    #     "interval",
    #     days=1,
    # )
    # scheduler.start()

    return app
