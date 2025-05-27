import os
from pathlib import Path

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from google.cloud import storage
from werkzeug.exceptions import NotFound, Unauthorized, BadRequest

from app.v1.models import User
from app.core.config import settings


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


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
            user_id = get_jwt_identity()
        except Exception as error:
            return Unauthorized(f"Token is invalid: {str(error)}")
        current_user = User.query.filter_by(id=int(user_id)).first()
        if not current_user:
            return NotFound(f"User {current_user.username} not found!")

        return func(current_user=current_user, *args, **kwargs)
    return wrapper	


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_upload_file(request):
    if 'file' not in request.files:
        raise BadRequest("No file part.")
    file = request.files.get("file")
    if file.filename == '':
        raise BadRequest("No selected file.")
    if not file or not allowed_file(file.filename):
        raise BadRequest("Invalid file type")
    return file


def find_file(filename: str, start_dir: Path = Path.cwd()) -> Path | None:
    for path in start_dir.rglob(filename):
        return path.resolve()
    return None or ""


def get_gcs_client():
    filepath = find_file(filename=settings.GCS_KEY)
    if os.path.isfile(filepath):
        client = storage.Client.from_service_account_json(filepath)
    else:
        client = storage.Client()
    return client