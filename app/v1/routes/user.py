from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest, NotFound

from app.core.database import db_session 
from app.v1.utils import api_response, token_required
from app.v1.models.user import User
from app.v1.schemas.user import UserEdit, UserRead
from app.v1.controllers.user import check_user_edit

user_bp = Blueprint('users', __name__, url_prefix='/users')


@user_bp.route('/profile', methods=['GET'])
@token_required
def view_profile(current_user: User):
    current_app.logger.info("View profile endpoint called!")
    response = UserRead.from_orm(current_user)
    return api_response(data=response.dict(), status=200)


@user_bp.route('/profile', methods=['PUT'])
@token_required
def edit_profile(current_user: User):
    current_app.logger.info("Edit profile endpoint called!")
    with db_session() as session:
        # current_app.logger.info("User edit with data:", request.get_json())
        json_data = request.get_json(force=True) or {}
        parsed_data = UserEdit.parse_obj(json_data)
        if not json_data:
            raise BadRequest("Please provide data to update.")
        #   Check username or email already exist
        check_user_edit(data=parsed_data, current_user=current_user)
        #   Update user profile
        for field_to_update, value in parsed_data.dict(exclude_unset=True).items():
            setattr(current_user, field_to_update, value)
        session.commit()
        current_app.logger.info(f"User {current_user.username} updated profile successfully.")
        response = UserRead.from_orm(current_user)
        return api_response(
            data=response.dict(), 
            message="Profile updated successfully.",
            status=200,
        )


@user_bp.route('/<int:user_id>/profile', methods=['GET'])
@token_required
def view_other_profile(user_id: int, current_user: User):
    current_app.logger.info("View other profile endpoint called!")
    user = User.query.get(user_id)
    if not user:
        raise NotFound(f"User with id {user_id} not found.")
    response = UserRead.from_orm(user)
    return api_response(data=response.dict(), status=200)