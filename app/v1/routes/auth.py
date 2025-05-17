from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app.core.database import db_session 
from app.v1.utils import api_response
from app.v1.schemas.user import UserCreate, UserRead, UserLoginResponse
from app.v1.controllers.user import create_user
from app.v1.controllers.auth import check_user_register, check_user_login


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    with db_session() as session:
        # 1. Serialize and validate input JSON with Pydantic
        data = UserCreate.parse_raw(request.data)
        check_user_register(data=data)
        #   2. Create user
        created_user = create_user(data=data, session=session)
        #   3. Deserialize User DB model to JSON response, convert from ORM-object to Pydantic object
        response = UserRead.from_orm(created_user)
        #   4. Commit the transaction if all operations are successful
        session.commit()
        return api_response(    
            data=response.dict(),   #   Also can be used as response.json()
            message='User registered successfully.', 
            status=201,
        )


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    user = check_user_login(username=username, password=password)
    #   Create access_token and refresh_token
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)
    
    response = UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserRead.from_orm(user)
    )

    return api_response(
        message='Login successfully.',
        data=response.dict(),
    )

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log out of the current user account."""
    # Since JWTs are stateless, we don't need to do anything here.
    # The client should simply discard the JWT token.
    return api_response(message='Logout successfully.')