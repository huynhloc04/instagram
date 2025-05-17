from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from werkzeug.exceptions import NotFound, Unauthorized

from app.v1.models import User

def api_response(data=None, message=None, status=200):
    response = {
        'success': 200 <= status < 300,
        'status': status
    }
    if message:
        response['message'] = message
    if data is not None:
        response['data'] = data
    return jsonify(response), status


def token_required(func):
    """Create decorator for API authentication using JWT"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            username = get_jwt_identity()
            
            current_user = User.query.filter_by(username=username).first()
            if not current_user:
                return NotFound(f"User {current_user.username} not found!")

            return func(current_user, *args, **kwargs)
        except Exception as error:
            return Unauthorized(f"Token is invalid: {str(error)}")
    return wrapper	
