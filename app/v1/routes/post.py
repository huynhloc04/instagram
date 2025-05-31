import re

from pydantic import ValidationError
from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest, NotFound, Conflict, Forbidden

from app.core.database import db_session
from app.v1.models import Post, User, Like, ImageCron
from app.v1.schemas.base import Pagination
from app.v1.schemas.post import PostCreate, PostEdit, PostReadList
from app.v1.controllers.post import create_post, update_post
from app.v1.controllers.tag import create_tags
from app.v1.enums import PostStatus, ImageCronEnum
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
    with db_session() as session:
        post = Post.query.get(post_id)
        if not post:
            raise NotFound("Post not found!")
        parsed_post = post.to_dict(
            current_user=current_user, 
            include_user=True, 
            include_like=True, 
            include_comment=True
        )
        current_app.logger.info(f"Post with id {post_id} retrieved successfully.")
        return api_response(
            data=parsed_post,
            message='Post retrieved successfully.',
            status=200,
        )

    
@postRoute.route("/news-feed", methods=["GET"])
@token_required
def view_news_feed(current_user: User):

    # Get pagination parameters from query string
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    with db_session() as session:
        posts = Post.query.filter_by(status=PostStatus.public.value, deleted=False) \
            .order_by(Post.created_at.desc())   \
            .paginate(page=page, per_page=per_page)
            
        news_feed = PostReadList(
            posts=[
                post.to_dict(
                    current_user=current_user, include_user=True, include_like=True
                )
                for post in posts
            ],
            pagination=Pagination(
                total=posts.total,
                page=posts.page,
                per_page=posts.per_page,
                pages=posts.pages,
            ),
        )
        current_app.logger.info("View news feed successfully.")
        return api_response(
            data=news_feed.model_dump(), message="View news feed successfully.", status=200
        )


@postRoute.route("/upload", methods=['POST'])
@token_required
def upload_media(current_user: User):
    #   1. Validate also prepare data
    uploaded_image = validate_upload_file(request=request)
    image_name = gcs_upload(file_obj=uploaded_image)
    #   2. Upload directly to Google Cloud Storage (GCS).
    current_app.logger.info("Upload media successfully.")

    with db_session() as session:
        image = ImageCron(
            image_name=image_name,
            status=ImageCronEnum.unused.value,
        )
        session.add(image)
        session.commit()
        
        return api_response(
            message="Upload media successfully.", 
            data={"image_id": image.id}, 
            status=201
        )


@postRoute.route("/draft", methods=['POST'])
@token_required
def create_draft_post(current_user: User):

    with db_session() as session:
        #   1. Validate also prepare data
        caption = request.form.get("caption")
        image_id = request.form.get("image_id")
        image = ImageCron.query.get(image_id)
        if not image:
            raise NotFound("Image not found.")

        #   2. Serialize and validate input JSON with Pydantic
        try:
            data_to_create_post = PostCreate(
                caption=caption,
                user_id=current_user.id,
                status=PostStatus.draft.value,
            )
        except ValidationError as exec:
            raise BadRequest(str(exec.errors()))

        #   3. Create instagram post and attach image to post
        draft_post = create_post(data=data_to_create_post, session=session)
        image.post_id = draft_post.id
        image.status = ImageCronEnum.used.value

        #   4. Create tag and attach tag to a post
        create_tags(post=create_post, session=session)

        session.commit()
        current_app.logger.info("Draft post created successfully.")
        
        return api_response(    
            data=draft_post.to_dict(include_user=True),   #   Also can be used as draft_post.json()
            message='Draft post created successfully.', 
            status=201,
        )


@postRoute.route("/", methods=['POST'])
@token_required
def create_post_public(current_user: User):

    with db_session() as session:
        caption = request.form.get("caption")
        image_id = request.form.get("image_id")
        image = ImageCron.query.get(image_id)
        if not image:
            raise NotFound("Image not found.")

        #   1. Serialize and validate input JSON with Pydantic
        try:
            data_to_create_post = PostCreate(
                caption=caption,
                user_id=current_user.id,
            )
        except ValidationError as exec:
            raise BadRequest(str(exec.error()))

        #   3. Create instagram post and attach image to post
        created_post = create_post(data=data_to_create_post, session=session)
        image.post_id = created_post.id
        image.status = ImageCronEnum.used.value

        #   4. Create tag and attach tag to a post
        create_tags(post=created_post, session=session)
        
        session.commit()
        current_app.logger.info("Post created successfully.")
        
        return api_response(    
            data=created_post.to_dict(include_user=True),
            message='Post created successfully.', 
            status=201,
        )


@postRoute.route("/<int:post_id>", methods=['PUT'])
@token_required
def update_post_public(post_id: int, current_user: User):

    with db_session() as session:
        existing_post = Post.query.get(post_id)

        if not existing_post:
            raise NotFound("Post not found!")
        if existing_post.user_id != current_user.id:
            raise Forbidden("You are not authorized to update this post!")
        if existing_post.status == PostStatus.public.value:
            raise BadRequest("Post already published")
            
        #   1. Validate also prepare data
        caption = request.form.get("caption")
        status = request.form.get("status")
        image_id = request.form.get("image_id")
        image = ImageCron.query.get(image_id)
        if not image:
            raise NotFound("Image not found.")

        #   2. Serialize and validate input JSON with Pydantic
        try:
            data_to_edit_post = PostEdit(
                caption=caption,
                user_id=current_user.id,
                status=status,
            )
        except ValidationError as exc:
            raise BadRequest(str(exc.error))

        #   3. Update instagram post
        updated_post = update_post(post=existing_post, data=data_to_edit_post)
        session.flush()
        image.post_id = updated_post.id
        image.status = ImageCronEnum.used.value
        session.commit()

        #   4. Deserialize User DB model to JSON response, convert from ORM-object to Pydantic object
        current_app.logger.info("Post updated successfully.")
        return api_response(    
            data=updated_post.to_dict(include_user=True),
            message='Post updated successfully.', 
            status=201,
        )


@postRoute.route("/<int:post_id>", methods=["DELETE"])
@token_required
def delete_post(post_id: int, current_user: User):

    with db_session() as session:
        existing_post = session.get(Post, post_id)
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
