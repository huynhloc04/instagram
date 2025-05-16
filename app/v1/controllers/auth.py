import re

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app.v1.utils import api_response
from app.v1 import users_db, root_bp

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    full_name = data.get('fullname')
    email = data.get('email')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    if username in users_db:
        return jsonify({'error': 'Username already exists'}), 400
    if not bool(EMAIL_REGEX.match(email)):
        return jsonify({'error': 'Invalid email format'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long'}), 400
    if not full_name:
        return jsonify({'error': 'Missing full name'}), 400

    pw_hash = generate_password_hash(password)
    profile = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "profile_picture": "blog.png",
        "bio": "",
        "created_at": int(datetime.now().timestamp())
    }
    users_db[username] = {'password': pw_hash, 'profile': profile}
    return api_response(data=profile, message='User registered successfully')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Login successful
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if username not in users_db:
        return jsonify({'error': 'Invalid username or password'}), 401

    if not check_password_hash(users_db[username]['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)

    return api_response(
        message='Login successful',
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": users_db[username]['profile'],
        })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log out of the current user account."""
    # Since JWTs are stateless, we don't need to do anything here.
    # The client should simply discard the JWT token.
    return api_response(message='Logout successful')