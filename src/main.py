import os
import re

from flask import Flask, request, jsonify
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    verify_jwt_in_request, 
    get_jwt_identity,
    JWTManager,
)


EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")   #   Regex Transform to validate email

app = Flask(__name__)
jwt = JWTManager(app)
app.secret_key = os.environ.get("SECRET_KEY", "__dev_secret_key__")

users_db = {}


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
            current_user = users_db.get(username)

            if not current_user:
                return api_response(message="User does not exist", status=404)

            return func(current_user, *args, **kwargs)
        except Exception as e:
            return api_response(message=f"Token is invalid: {str(e)}", status=401)
    return wrapper	


@app.route('/register', methods=['POST'])
def register():
    """To register a new account"""

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


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    # Kiểm tra xem tên đăng nhập có tồn tại trong hệ thống hay không
    if username not in users_db:
        return jsonify({'error': 'Invalid username or password'}), 401

    # Kiểm tra mật khẩu đã nhập có khớp với mật khẩu đã mã hóa hay không
    if not check_password_hash(users_db[username]['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Nếu tên đăng nhập và mật khẩu đều đúng, tạo access token và refresh token
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)

    # Trả về response thành công kèm theo token và thông tin người dùng
    return api_response(
        message='Login successful',
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": users_db[username]['profile'],
        })


@app.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """UC04: Lấy thông tin hồ sơ của người dùng hiện tại."""
    return api_response(data=current_user['profile'])


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
