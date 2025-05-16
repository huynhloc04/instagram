from flask import Blueprint

from app.v1.utils import api_response, token_required
from app.v1 import root_bp

user_bp = Blueprint('users', __name__, url_prefix='/users')


@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return api_response(data=current_user['profile'])
