#   Reference: https://medium.com/@dmostoller/mastering-error-handling-in-flask-with-werkzeug-exceptions-ensuring-robust-server-side-validations-a00a9862566a

from flask import Flask, current_app
from werkzeug.exceptions import (
    Conflict,
    Unauthorized,
    Forbidden,
    NotFound,
    BadRequest,
    InternalServerError,
)

from app.v1.utils import api_response


def log_http_error(error, status_code: int):
    if status_code >= 500:
        current_app.logger.error(
            str(error),
            exc_info=True
        )
    else:
        current_app.logger.warning(
            str(error),
            exc_info=True
        )


def register_error_handlers(app: Flask):

    @app.errorhandler(BadRequest)
    def handle_bad_request_error(error):
        log_http_error(error=error, status_code=400)
        return api_response(message=str(error), status=400)

    @app.errorhandler(Unauthorized)
    def handle_unauthorized_error(error):
        log_http_error(error=error, status_code=401)
        return api_response(message=str(error), status=401)

    @app.errorhandler(Forbidden)
    def handle_forbidden_error(error):
        log_http_error(error=error, status_code=403)
        return api_response(message=str(error), status=403)

    @app.errorhandler(NotFound)
    def handle_not_found_error(error):
        log_http_error(error=error, status_code=404)
        return api_response(message=str(error), status=404)

    @app.errorhandler(Conflict)
    def handle_conflict_error(error):
        log_http_error(error=error, status_code=409)
        return api_response(message=str(error), status=409)

    @app.errorhandler(InternalServerError)
    def handle_internal_server_error(error):
        log_http_error(error=error, status_code=500)
        return api_response(message=str(error), status=500)

    # @app.errorhandler(429)
    # def handle_rate_limit_error(error):
    #     # Try to extract headers from the error if available
    #     headers = getattr(error, 'headers', {}) or {}
    #     response = api_response(
    #         message=str(error.description) if hasattr(error, 'description') else "Too many requests.",
    #         status=429
    #     )
    #     # Attach rate limit headers if present
    #     for header in [
    #         "Retry-After",
    #         "X-RateLimit-Limit",
    #         "X-RateLimit-Remaining",
    #         "X-RateLimit-Reset"
    #     ]:
    #         if header in headers:
    #             response.headers[header] = headers[header]
    #     return response
