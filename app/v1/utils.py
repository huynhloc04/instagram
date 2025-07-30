import os, time
from pathlib import Path
import cProfile
import pstats
import io
from functools import wraps
from datetime import datetime

from flask import jsonify, request, g
from functools import wraps
from google.cloud import storage
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import NotFound, Unauthorized, BadRequest

from app.v1.models import User
from app.core.config import settings
from app.logs.config import REQUEST_COUNT, REQUEST_LATENCY


ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}


def api_response(data=None, message=None, status=200):
    response = {"success": 200 <= status < 300, "status": status}
    if message:
        response["message"] = message
    if data is not None:
        response["data"] = data
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


def user_or_ip_key():
    json_data = request.get_json(silent=True) or {}
    username = json_data.get("username")
    if username:
        return f"username:{username}"
    return f"ip:{get_remote_address()}"


def user_id_from_token_key():
    """
    Returns a unique key for the current user based on JWT token identity.
    Falls back to IP address if no valid token is present.
    """
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            return f"user_id:{user_id}"
    except Exception:
        pass
    return f"ip:{get_remote_address()}"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_upload_file(request):
    if "file" not in request.files:
        raise BadRequest("No file part.")
    file = request.files.get("file")
    if file.filename == "":
        raise BadRequest("No selected file.")
    if not file or not allowed_file(file.filename):
        raise BadRequest("Invalid file type")
    return file


def find_file(filename: str, start_dir: Path = Path.cwd()) -> Path | None:
    for path in start_dir.rglob(filename):
        return path.resolve()
    return None or ""


def register_dependencies(app):

    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def record_metrics(response):
        start_time = getattr(g, "start_time", None)
        if start_time is not None:
            latency = time.time() - start_time
            REQUEST_COUNT.labels(
                request.method, request.path, response.status_code
            ).inc()
            REQUEST_LATENCY.labels(request.method, request.path).observe(latency)
        return response


def cprofile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cprofile directory if it doesn't exist
        profile_dir = "cprofile/"
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_path = os.path.join(profile_dir, f"{func.__name__}_{timestamp}.prof")

        pr = cProfile.Profile()
        pr.enable()

        result = func(*args, **kwargs)

        pr.disable()

        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.dump_stats(profile_path)
        return result

    return wrapper
