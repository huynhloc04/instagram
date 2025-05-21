from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest, NotFound, Conflict

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


@userRoute.route('/profile', methods=['GET'])
@token_required
def view_profile(current_user: User):
    current_app.logger.info("View profile endpoint called!")
    user_profile = current_user.to_dict(
        viewer=current_user, excludes=["is_following"]
    )
    return api_response(data=user_profile, status=200)


@userRoute.route('/profile', methods=['PUT'])
@token_required
def edit_profile(current_user: User):
    current_app.logger.info("Edit profile endpoint called!")
    
    with db_session() as session:
        json_data = request.get_json(force=True) or {}
        if not json_data:
            raise BadRequest("Please provide data to update.")
        try:
            parsed_data = UserEdit.parse_obj(json_data)
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
        updated_profile = UserRead.from_orm(current_user)
        return api_response(
            data=updated_profile.dict(), 
            message="Profile updated successfully.",
            status=200,
        )


@userRoute.route('/<int:user_id>/profile', methods=['GET'])
@token_required
def view_other_profile(user_id: int, current_user: User):
    current_app.logger.info("View other profile endpoint called!")
    user = User.query.get(user_id)
    if not user:
        raise NotFound(f"User with id {user_id} not found.")
    # response = UserRead.from_orm(user)
    # return api_response(data=response.dict(), status=200)
    user_profile = user.to_dict(viewer=current_user)
    return api_response(data=user_profile, status=200)


@userRoute.route("/<int:user_id>/posts", methods=['GET'])
@token_required
def get_list_post(user_id: int, current_user: User):
    current_app.logger.info("Retieve all posts endpoint called.")
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
            data=post_list.dict(),
            message='Retrieved all posts successfully.',
            status=200,
        )


@userRoute.route("/<int:user_id>/follow", methods=['POST'])
@token_required
def follow_user(user_id: int, current_user: User):
    current_app.logger.info("Follow user endpoint called.")
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
    current_app.logger.info("Unfollow user endpoint called.")
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
    current_app.logger.info("Get follower endpoint called.")
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
                UserRead.from_orm(result) for result in results
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
            data=followers.dict(), message="Get follower users successfully.", status=200
        )


@userRoute.route("/<int:user_id>/followings", methods=['GET'])
@token_required
def get_following(user_id: int, current_user: User):
    """Get all users who the user {user_id} followed """
    current_app.logger.info("Get following endpoint called.")
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
                UserRead.from_orm(result) for result in results
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
            data=followers.dict(), message="Get followings users successfully.", status=200
        )