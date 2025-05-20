import time
import os

from pydantic import ValidationError
from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest, NotFound, Forbidden, InternalServerError

from app.core.database import db_session
from app.core.config import settings
from app.v1.models import Post, User
from app.v1.schemas.post import PostCreate, PostRead, PostEdit, PostReadList
from app.v1.controllers.post import create_post, update_post, handle_upload_image
from app.v1.enums import PostStatus
from app.v1.utils import (
    api_response, 
    token_required, 
    validate_upload_file,
)

postRoute = Blueprint('posts', __name__, url_prefix='/posts')


@postRoute.route("/<int:post_id>", methods=['GET'])
@token_required
def get_post(post_id: int, current_user: User):
    current_app.logger.info("Retieve post endpoint called.")
    with db_session() as session:
        post = Post.query.filter(Post.id == post_id).first()
        if not post:
            raise NotFound("Post not found!")
        response = PostRead.from_post(post, include_user=True)
        current_app.logger.info(f"Post with id {post_id} retrieved successfully.")
        return api_response(
            data=response.dict(),
            message='Post retrieved successfully.',
            status=200,
        )


@postRoute.route("/draft", methods=['POST'])
@token_required
def create_draft_post(current_user: User):
    current_app.logger.info("Create draft post endpoint called.")

    with db_session() as session:
        #   1. Validate also prepare data
        uploaded_image = validate_upload_file(request=request)
        image_name = handle_upload_image(image=uploaded_image)
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
        created_post = create_post(data=data_to_create_post, session=session)
        session.commit()

        #   4. Deserialize User DB model to JSON response, convert from ORM-object to Pydantic object
        current_app.logger.info("Draft post created successfully.")
        response = PostRead.from_post(created_post, include_user=True)
        
        return api_response(    
            data=response.dict(),   #   Also can be used as response.json()
            message='Draft post created successfully.', 
            status=201,
        )


@postRoute.route("/", methods=['POST'])
@token_required
def create_post_public(current_user: User):
    current_app.logger.info("Create post endpoint called.")

    with db_session() as session:
        #   1. Validate also prepare data
        uploaded_image = validate_upload_file(request=request)
        image_name = handle_upload_image(image=uploaded_image)
        caption = request.form.get("caption")

        #   2. Serialize and validate input JSON with Pydantic
        try:
            data_to_create_post = PostCreate(
                caption=caption,
                image_name=image_name,
                user_id=current_user.id,
                status=PostStatus.PUBLIC,
            )
        except ValidationError as exec:
            raise BadRequest(str(exec.error()))

        #   3. Create instagram post
        created_post = create_post(data=data_to_create_post, session=session)
        session.commit()
        
        #   4. Deserialize User DB model to JSON response, convert from ORM-object to Pydantic object
        current_app.logger.info("Post created successfully.")
        
        response = PostRead.from_post(post=created_post, include_user=True)
        return api_response(    
            data=response.dict(),
            message='Post created successfully.', 
            status=201,
        )


@postRoute.route("/<int:post_id>", methods=['PUT'])
@token_required
def update_post_public(post_id: int, current_user: User):
    current_app.logger.info("Update post endpoint called.")

    with db_session() as session:
        existing_post = Post.query.get(post_id).first()

        if not existing_post:
            raise NotFound("Post not found!")
        if existing_post.user_id != current_user.id:
            raise Forbidden("You are not authorized to update this post!")
        if existing_post.status == PostStatus.PUBLIC:
            raise BadRequest("Post already published")
            
        #   1. Validate also prepare data
        image_name = None
        if 'file' in request.files:
            uploaded_image = validate_upload_file(request=request)
            image_name = handle_upload_image(image=uploaded_image)
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
        update_post(post=existing_post, data=data_to_edit_post, session=session)
        session.commit()

        #   4. Deserialize User DB model to JSON response, convert from ORM-object to Pydantic object
        current_app.logger.info("Post updated successfully.")
        response = PostRead.from_post(post=existing_post, include_user=True)
        return api_response(    
            data=response.dict(),
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