from flask import Blueprint, current_app, request
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, NotFound, Conflict, InternalServerError

from app.core.database import db_session 
from app.v1.utils import api_response, token_required
from app.v1.models import User, Post, Follow
from app.v1.schemas.base import Pagination
from app.v1.schemas.user import UserEdit, UserRead, UserReadList
from app.v1.schemas.post import PostReadList, PostRead
from app.v1.schemas.follow import FollowUser
from app.v1.controllers.user import check_user_edit
from app.v1.controllers.follow import create_follow_user

userRoute = Blueprint('users', __name__, url_prefix='/users')


@userRoute.route('/me', methods=['GET'])
@token_required
def view_profile(current_user: User):
    try:
        user_profile = current_user.to_dict(
            viewer=current_user, excludes=["is_following"]
        )
    except ValueError as error:
        raise InternalServerError(f"Error while fetching user {current_user.id} profile.")
    current_app.logger.info(f"Get profile of user {current_user.id} successfully.")
    return api_response(
        data=user_profile, message="Get user profile successfully.", status=200
    )


@userRoute.route('/profile', methods=['PUT'])
@token_required
def edit_profile(current_user: User):
    
    with db_session() as session:
        json_data = request.get_json(force=True) or {}
        if not json_data:
            raise BadRequest("Please provide data to update.")
        try:
            parsed_data = UserEdit.model_validate(json_data)
        except ValidationError as exec:
            raise BadRequest(str(exec.error()))

        #   Check username or email already exist
        check_user_edit(data=parsed_data, current_user=current_user)
        #   Update user profile
        for field_to_update, value in parsed_data.dict(
            exclude_unset=True, exclude_none=True
        ).items():
            setattr(current_user, field_to_update, value)
        session.commit()

        current_app.logger.info(f"User {current_user.username} updated profile successfully.")
        updated_profile = UserRead.model_validate(current_user)
        return api_response(
            data=updated_profile.model_dump(), 
            message="Profile updated successfully.",
            status=200,
        )


@userRoute.route('/<int:user_id>/profile', methods=['GET'])
@token_required
def view_other_profile(user_id: int, current_user: User):
    user = User.query.get(user_id)
    if not user:
        raise NotFound(f"User with id {user_id} not found.")
    # response = UserRead.model_validate(user)
    # return api_response(data=response.dict(), status=200)
    user_profile = user.to_dict(viewer=current_user)
    return api_response(data=user_profile, status=200)


@userRoute.route("/<int:user_id>/posts", methods=['GET'])
@token_required
def get_list_post(user_id: int, current_user: User):
    with db_session() as session:
        # Get pagination parameters from query string
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        posts = Post.query.filter(
            Post.user_id==user_id, Post.deleted==False
        ).order_by(
            Post.created_at.desc()
        ).paginate(page=page, per_page=per_page)

        post_list = PostReadList(
            posts=[PostRead.from_post(post, include_user=True) for post in posts.items],
            pagination=Pagination(
                page=posts.page,
                per_page=posts.per_page,
                total=posts.total,
                pages=posts.pages
            )
        )
        current_app.logger.info(f"Retrieved all posts for user {current_user.id} successfully.")
        return api_response(
            data=post_list.model_dump(),
            message='Retrieved all posts successfully.',
            status=200,
        )


@userRoute.route("/<int:user_id>/follow", methods=['POST'])
@token_required
def follow_user(user_id: int, current_user: User):

    with db_session() as session:
        user = User.query.get(user_id)
        if not user:
            raise NotFound("Following user not found!")
        if user_id == current_user.id:
            raise Conflict("Canot follow yourself.")
        is_following = Follow.query.filter_by(
            follower_id=current_user.id, following_id=user_id
        ).first()
        if is_following:
            raise Conflict("You are already following this user.")

        create_follow_user(
            data=FollowUser(follower_id=current_user.id, following_id=user_id),
            session=session
        )
        session.commit()
        current_app.logger.info(f"You followed user {user.username} successfully.")
        return api_response(message="Follow user successfully.")


@userRoute.route("/<int:user_id>/unfollow", methods=['DELETE'])
@token_required
def unfollow_user(user_id: int, current_user: User):

    with db_session() as session:
        user = User.query.get(user_id)
        if not user:
            raise NotFound("The following user not found!")
        if user_id == current_user.id:
            raise Conflict("Canot unfollow yourself.")
        is_following = Follow.query.filter_by(
            follower_id=current_user.id, following_id=user_id
        ).first()
        if not is_following:
            raise Conflict("You have not followed this user yet.")

        session.delete(is_following)
        session.commit()
        current_app.logger.info(f"You unfollowed user {user.username} successfully.")
        return api_response(message="Unfollow user successfully.")


@userRoute.route("/<int:user_id>/followers", methods=['GET'])
@token_required
def get_follower(user_id: int, current_user: User):
    """Get all users who follow the user {user_id} """

    with db_session() as session:

        # Get pagination parameters from query string
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        user = User.query.get(user_id)
        if not user:
            raise NotFound("Follower not found!")

        results = session.query(User).join(
            Follow, Follow.follower_id==User.id
        ).filter(
            Follow.following_id==user_id
        ).order_by(
            User.created_at.desc()
        ).paginate(page=page, per_page=per_page)

        followers = UserReadList(
            users=[
                UserRead.model_validate(result) for result in results
            ],
            pagination=Pagination(
                page=results.page,
                per_page=results.per_page,
                total=results.total,
                pages=results.pages
            )
        )
        current_app.logger.info(f"Retrieved all followers for user {user.id} successfully.")
        return api_response(
            data=followers.model_dump(), message="Get follower users successfully.", status=200
        )


@userRoute.route("/<int:user_id>/followings", methods=['GET'])
@token_required
def get_following(user_id: int, current_user: User):
    """Get all users who the user {user_id} followed """

    with db_session() as session:
        # Get pagination parameters from query string
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        user = User.query.get(user_id)
        if not user:
            raise NotFound("Follower not found!")

        results = session.query(User).join(
            Follow, Follow.following_id==User.id
        ).filter(
            Follow.follower_id==user_id
        ).order_by(
            User.created_at.desc()
        ).paginate(page=page, per_page=per_page)

        followers = UserReadList(
            users=[
                UserRead.model_validate(result) for result in results
            ],
            pagination=Pagination(
                page=results.page,
                per_page=results.per_page,
                total=results.total,
                pages=results.pages
            )
        )
        current_app.logger.info(f"Retrieved all followings for user {user.id} successfully.")
        return api_response(
            data=followers.model_dump(), message="Get followings users successfully.", status=200
        )


@userRoute.route("/search", methods=["GET"])
@token_required
def search_user(current_user: User):
    username = request.args.get('username', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    with db_session() as session:
        users = User.query.filter(User.username.like(f"%{username}%")).paginate(
            page=page, per_page=per_page
        )
        results = UserReadList(
            users=[
                UserRead.model_validate(user) for user in users
            ],
            pagination=Pagination(
                total=users.total,
                page=users.page,
                per_page=users.per_page,
                pages=users.pages,
            )
        )
        return api_response(
            data=results.model_dump(), message="Search user successfully.", status=200
        )