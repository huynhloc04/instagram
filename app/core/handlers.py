#   Reference: https://medium.com/@dmostoller/mastering-error-handling-in-flask-with-werkzeug-exceptions-ensuring-robust-server-side-validations-a00a9862566a

from flask import Flask, jsonify
from werkzeug.exceptions import (
    Conflict, 
    Unauthorized, 
    Forbidden, 
    NotFound, 
    BadRequest, 
    InternalServerError
)

from app.v1.utils import api_response


def register_error_handlers(app: Flask):

    @app.errorhandler(BadRequest)
    def handle_bad_request_error(error):
        return api_response(message=str(error), status=400)

    @app.errorhandler(Unauthorized)
    def handle_bad_request_error(error):
        return api_response(message=str(error), status=401)

    @app.errorhandler(Forbidden)
    def handle_bad_request_error(error):
        return api_response(message=str(error), status=403)

    @app.errorhandler(NotFound)
    def handle_not_found_error(error):
        return api_response(message=str(error), status=404)

    @app.errorhandler(Conflict)
    def handle_conflict_error(error):
        return api_response(message=str(error), status=409)

    @app.errorhandler(InternalServerError)
    def handle_internal_server_error(error):
        return api_response(message=str(error), status=500)
