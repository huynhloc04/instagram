from datetime import timedelta

from pydantic import ValidationError
from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.exceptions import BadRequest

from app.core.database import db_session 
from app.core.config import settings
from app.v1.utils import api_response
from app.v1.schemas.user import UserCreate, UserRead, UserLoginResponse
from app.v1.controllers.user import create_user
from app.v1.controllers.auth import check_user_register, check_user_login


authRoute = Blueprint('auth', __name__, url_prefix='/auth')

@authRoute.route('/register', methods=['POST'])
def register():

    with db_session() as session:
        # 1. Serialize and validate input JSON with Pydantic
        json_data = request.get_json()
        if not json_data:
            raise BadRequest("Please provide data to update.")
        try:
            parsed_data = UserCreate.model_validate(json_data)
        except ValidationError as exec:
            raise BadRequest(str(exec.error()))
        
        check_user_register(data=parsed_data)

        #   2. Create user
        created_user = create_user(data=parsed_data, session=session)
        session.commit()
        
        #   3. Deserialize User DB model to JSON response, convert from ORM-object to Pydantic object
        registerd_user = UserRead.model_validate(created_user)
        current_app.logger.info(f"User registered with username: {created_user.username} successfully.")
        return api_response(    
            data=registerd_user.model_dump(),   #   Also can be used as registerd_user.json()
            message='User registered successfully.', 
            status=201,
        )


@authRoute.route('/login', methods=['POST'])
def login():

    json_data = request.get_json()
    if not json_data:
        raise BadRequest("Please provide data to update.")
    username = json_data.get('username')
    password = json_data.get('password')

    user = check_user_login(username=username, password=password)
    #   Create access_token and refresh_token
    access_token = create_access_token(
        identity=str(user.id), 
        expires_delta=timedelta(minutes=int(settings.JWT_ACCESS_TOKEN_EXPIRES))
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        expires_delta=timedelta(minutes=int(settings.JWT_REFRESH_TOKEN_EXPIRES))
    )
    
    login_user = UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserRead.model_validate(user)
    )
    current_app.logger.info(f"User {username} login successfully.")
    return api_response(
        message='Login successfully.',
        data=login_user.model_dump(),
        status=200,
    )


@authRoute.route('/logout', methods=['POST'])
def logout():
    # Since JWTs are stateless, we don't need to do anything here.
    # The client should simply discard the JWT token.
    return api_response(message='Logout successfully.')
