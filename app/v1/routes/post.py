import time
import os

from pydantic import ValidationError
from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest, NotFound, Conflict, Forbidden, InternalServerError

from app.core.database import db_session
from app.core.config import settings
from app.v1.models import Post, User, Like
from app.v1.schemas.post import PostCreate, PostRead, PostEdit, PostReadList
from app.v1.controllers.post import create_post, update_post
from app.v1.enums import PostStatus
from app.v1.utils import (
    api_response, 
    token_required, 
    validate_upload_file,
)
from app.v1.storage import gcs_upload


postRoute = Blueprint('posts', __name__, url_prefix='/posts')


@postRoute.route("/<int:post_id>", methods=['GET'])
@token_required
def get_post(post_id: int, current_user: User):
    current_app.logger.info("Retieve post endpoint called.")
    with db_session() as session:
        post = Post.query.get(post_id)
        if not post:
            raise NotFound("Post not found!")
        parsed_post = post.to_dict(
            current_user=current_user, include_user=True, include_like=True
        )
        current_app.logger.info(f"Post with id {post_id} retrieved successfully.")
        return api_response(
            data=parsed_post,
            message='Post retrieved successfully.',
            status=200,
        )


@postRoute.route("/upload", methods=['POST'])
@token_required
def upload_media(current_user: User):
    current_app.logger.info("Post upload media endpoint called.")
    #   1. Validate also prepare data
    uploaded_image = validate_upload_file(request=request)
    image_name = gcs_upload(file_obj=uploaded_image)
    #   2. Upload directly to Google Cloud Storage (GCS).
    current_app.logger.info("Upload media successfully.")
    return api_response(
        message="Upload media successfully.", data=image_name, status=200
    )


@postRoute.route("/draft", methods=['POST'])
@token_required
def create_draft_post(current_user: User):
    current_app.logger.info("Create draft post endpoint called.")

    with db_session() as session:
        #   1. Validate also prepare data
        image_name = request.form.get("image_name")
        caption = request.form.get("caption")

        #   2. Serialize and validate input JSON with Pydantic
        try:
            data_to_create_post = PostCreate(
                caption=caption,
                image_name=image_name,
                user_id=current_user.id,
                status=PostStatus.DRAFT,
            )
        except ValidationError as exec:
            raise BadRequest(str(exec.error()))

        #   3. Create instagram post
        draft_post = create_post(data=data_to_create_post, session=session)
        session.commit()

        #   4. Deserialize User DB model to JSON response, convert from ORM-object to Pydantic object
        current_app.logger.info("Draft post created successfully.")
        # draft_post = PostRead.from_post(created_post, include_user=True)
        
        return api_response(    
            data=draft_post.to_dict(include_user=True),   #   Also can be used as draft_post.json()
            message='Draft post created successfully.', 
            status=201,
        )


@postRoute.route("/", methods=['POST'])
@token_required
def create_post_public(current_user: User):
    current_app.logger.info("Create post endpoint called.")

    with db_session() as session:
        image_name = request.form.get("image_name")
        caption = request.form.get("caption")

        #   1. Serialize and validate input JSON with Pydantic
        try:
            data_to_create_post = PostCreate(
                caption=caption,
                image_name=image_name,
                user_id=current_user.id,
            )
        except ValidationError as exec:
            raise BadRequest(str(exec.error()))

        #   3. Create instagram post
        created_post = create_post(data=data_to_create_post, session=session)
        session.commit()
        
        #   4. Deserialize User DB model to JSON response, convert from ORM-object to Pydantic object
        current_app.logger.info("Post created successfully.")
        
        # created_post = PostRead.from_post(post=created_post, include_user=True)
        return api_response(    
            data=created_post.to_dict(include_user=True),
            message='Post created successfully.', 
            status=201,
        )


@postRoute.route("/<int:post_id>", methods=['PUT'])
@token_required
def update_post_public(post_id: int, current_user: User):
    current_app.logger.info("Update post endpoint called.")

    with db_session() as session:
        existing_post = Post.query.get(post_id)

        if not existing_post:
            raise NotFound("Post not found!")
        if existing_post.user_id != current_user.id:
            raise Forbidden("You are not authorized to update this post!")
        if existing_post.status == PostStatus.PUBLIC:
            raise BadRequest("Post already published")
            
        #   1. Validate also prepare data
        image_name = request.form.get("image_name")
        caption = request.form.get("caption")
        status = request.form.get("status")

        #   2. Serialize and validate input JSON with Pydantic
        try:
            data_to_edit_post = PostEdit(
                caption=caption,
                image_name=image_name,
                user_id=current_user.id,
                status=status,
            )
        except ValidationError as exc:
            raise BadRequest(str(exc.error))

        #   3. Update instagram post
        updated_post = update_post(post=existing_post, data=data_to_edit_post, session=session)
        session.commit()

        #   4. Deserialize User DB model to JSON response, convert from ORM-object to Pydantic object
        current_app.logger.info("Post updated successfully.")
        # updated_post = PostRead.from_post(post=existing_post, include_user=True)
        return api_response(    
            data=updated_post.to_dict(include_user=True),
            message='Post updated successfully.', 
            status=201,
        )


@postRoute.route("/<int:post_id>", methods=["DELETE"])
@token_required
def delete_post(post_id: int, current_user: User):
    current_app.logger.info("Delete post endpoint called.")

    with db_session() as session:
        existing_post = Post.query.get(post_id)
        if not existing_post or existing_post.deleted==True:
            raise NotFound("Post not found!")
        if existing_post.user_id != current_user.id:
            raise Forbidden("You are not authorized to delete this post!")

        #   Delete post
        existing_post.deleted = True
        session.commit()
        return api_response(
            message='Post deleted successfully.',
            status=200,
        )


@postRoute.route("/<int:post_id>/likes", methods=["POST"])
@token_required
def like_post(post_id: int, current_user: User):
    current_app.logger.info("Like post endpoint called.")
    
    with db_session() as session:
        post = Post.query.get(post_id)
        if not post:
            raise NotFound(f"Post {post_id} not found.")
        is_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
        if is_like:
            raise Conflict("You have already liked this post.")
        #   Like a post
        like = Like(user_id=current_user.id, post_id=post_id)
        session.add(like)
        session.commit()
        current_app.logger.info(f"User {current_user.id} liked post {post_id} successfully.")
        return api_response(message="Like post successfully!")


@postRoute.route("/<int:post_id>/unlikes", methods=["POST"])
@token_required
def unlike_post(post_id: int, current_user: User):
    current_app.logger.info("Unlike post endpoint called.")
    
    with db_session() as session:
        post = Post.query.get(post_id)
        if not post:
            raise NotFound(f"Post {post_id} not found.")
        is_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
        if not is_like:
            raise Conflict("You have not liked this post yet.")
        #   Unlike a post
        session.delete(is_like)
        session.commit()
        current_app.logger.info(f"User {current_user.id} unliked post {post_id} successfully.")
        return api_response(message="Unlike post successfully!")