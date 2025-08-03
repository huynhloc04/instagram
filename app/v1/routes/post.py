from pydantic import ValidationError
from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest, NotFound, Conflict, Forbidden
from flask_limiter.util import get_remote_address
from flask_jwt_extended import jwt_required

from app.core.extensions import limiter
from app.core.database import db_session
from app.v1.models import Post, User, Like, ImageCron, Comment, PostTag, Tag
from app.v1.schemas.base import Pagination
from app.v1.schemas.post import PostCreate, PostEdit, PostReadList
from app.v1.schemas.comment import CommentReadList, CommentTree
from app.v1.services.post import create_post, update_post
from app.v1.services.tag import create_tags
from app.v1.enums import PostStatus, ImageCronEnum
from app.v1.storage import _generate_put_singed_url, _generate_get_singed_url
from app.v1.services.comment import get_base_comment_and_count
from app.v1.utils import user_id_from_token_key
from app.v1.utils import (
    api_response,
    token_required,
)


postRoute = Blueprint("posts", __name__, url_prefix="/posts")


@postRoute.route("/<int:post_id>", methods=["GET"])
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
            include_comment=True,
        )
        current_app.logger.info(f"Post with id {post_id} retrieved successfully.")
        return api_response(
            data=parsed_post,
            message="Post retrieved successfully.",
            status=200,
        )


@postRoute.route("/news-feed", methods=["GET"])
@token_required
def view_news_feed(current_user: User):

    # Get pagination parameters from query string
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    with db_session() as session:
        posts = (
            Post.query.filter_by(status=PostStatus.public.value, deleted=False)
            .order_by(Post.created_at.desc())
            .paginate(page=page, per_page=per_page)
        )

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
            data=news_feed.model_dump(),
            message="View news feed successfully.",
            status=200,
        )


@postRoute.route("/sign-url", methods=["POST"])
@token_required
def get_signed_url(current_user: User):
    #   1. Validate also prepare data
    filename = request.form.get("filename", "default.png", type=str)
    expiration = request.form.get("expiration", 60, type=int)

    #   2. Get presigned url information
    presigned_dict = _generate_put_singed_url(filename=filename, expiration=expiration)

    return api_response(
        message="Get signed url successfully.",
        data=presigned_dict,
        status=201,
    )


@postRoute.route("/save-image", methods=["POST"])
@token_required
def save_image(current_user: User):
    #   1. Validate also prepare data
    filename = request.form.get("filename", "default.png", type=str)
    if not filename:
        raise BadRequest("Filename is required.")

    #   2. Save image to database
    with db_session() as session:
        image = ImageCron(
            image_name=filename,
            status=ImageCronEnum.unused.value,
        )
        session.add(image)
        session.commit()

        return api_response(
            message="Save image successfully.",
            status=201,
            data={"image_id": image.id},
        )


@postRoute.route("/get-image", methods=["GET"])
@token_required
def get_image(current_user: User):
    image_id = request.form.get("image_id", type=int)
    with db_session() as session:
        image = session.query(ImageCron).filter(ImageCron.id == image_id).first()
        if not image:
            raise NotFound("Image not found.")
    singed_url = _generate_get_singed_url(filename=image.image_name)
    return api_response(message="Get image successfully.", status=200, data=singed_url)


@postRoute.route("/draft", methods=["POST"])
@token_required
@limiter.limit(
    "10/hour",
    key_func=user_id_from_token_key,
    error_message="Too many create draft post attempts. Please try again later.",
)
def create_draft_post(current_user: User):

    with db_session() as session:
        #   1. Validate also prepare data
        json_data = request.get_json()
        if not json_data:
            raise BadRequest("Please provide data to update.")
        caption = json_data.get("caption")
        image_id = json_data.get("image_id")
        image = session.query(ImageCron).filter(ImageCron.id == image_id).first()
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
            data=draft_post.to_dict(
                include_user=True
            ),  #   Also can be used as draft_post.json()
            message="Draft post created successfully.",
            status=201,
        )


@postRoute.route("/", methods=["POST"])
@token_required
@limiter.limit(
    "10/hour",
    key_func=user_id_from_token_key,
    error_message="Too many create post attempts. Please try again later.",
)
def create_post_public(current_user: User):

    with db_session() as session:
        json_data = request.get_json()
        if not json_data:
            raise BadRequest("Please provide data to update.")
        caption = json_data.get("caption")
        image_id = json_data.get("image_id")
        image = session.query(ImageCron).filter(ImageCron.id == image_id).first()
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
            message="Post created successfully.",
            status=201,
        )


@postRoute.route("/<int:post_id>", methods=["PUT"])
@token_required
@limiter.limit(
    "10/hour",
    key_func=user_id_from_token_key,
    error_message="Too many update post attempts. Please try again later.",
)
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
        json_data = request.get_json()
        if not json_data:
            raise BadRequest("Please provide data to update.")
        caption = json_data.get("caption")
        image_id = json_data.get("image_id")
        status = json_data.get("status")
        image = session.query(ImageCron).filter(ImageCron.id == image_id).first()
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
            message="Post updated successfully.",
            status=201,
        )


@postRoute.route("/<int:post_id>", methods=["DELETE"])
@token_required
@limiter.limit(
    "10/hour",
    key_func=user_id_from_token_key,
    error_message="Too many delete post attempts. Please try again later.",
)
def delete_post(post_id: int, current_user: User):

    with db_session() as session:
        existing_post = session.get(Post, post_id)
        if not existing_post or existing_post.deleted == True:
            raise NotFound("Post not found!")
        if existing_post.user_id != current_user.id:
            raise Forbidden("You are not authorized to delete this post!")

        #   Delete post
        existing_post.deleted = True
        session.commit()
        return api_response(
            message="Post deleted successfully.",
            status=200,
        )


@postRoute.route("/<int:post_id>/likes", methods=["POST"])
@token_required
@limiter.limit(
    "60/minute",
    key_func=user_id_from_token_key,
    error_message="Too many like post attempts. Please try again later.",
)
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
        current_app.logger.info(
            f"User {current_user.id} liked post {post_id} successfully."
        )
        return api_response(message="Like post successfully!")


@postRoute.route("/<int:post_id>/unlikes", methods=["POST"])
@token_required
@limiter.limit(
    "60/minute",
    key_func=user_id_from_token_key,
    error_message="Too many unlike post attempts. Please try again later.",
)
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
        current_app.logger.info(
            f"User {current_user.id} unliked post {post_id} successfully."
        )
        return api_response(message="Unlike post successfully!")


@postRoute.route("/<int:post_id>/comments", methods=["GET"])
@token_required
def list_base_comments(post_id: int, current_user: User):

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    with db_session() as session:
        post = session.query(Post).where(Post.id == post_id).first()
        if not post:
            raise NotFound(f"Post {post_id} not found!")

        comments = get_base_comment_and_count(post_id=post_id, session=session)

        current_app.logger.info(f"View all comments for post {post_id} successfully.")
        return api_response(
            data=comments, message="View comments successfully.", status=200
        )


@postRoute.route("/<int:post_id>/comments/<int:comment_id>", methods=["GET"])
@token_required
def list_child_comments(post_id: int, comment_id: int, current_user: User):

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    with db_session() as session:
        post = session.query(Post).where(Post.id == post_id).first()
        if not post:
            raise NotFound(f"Post {post_id} not found!")

        results = (
            session.query(Comment)
            .where(
                Comment.parent_comment_id == comment_id,
                Comment.post_id == post_id,
                Comment.parent_comment_id is not None,
            )
            .order_by(Comment.created_at.desc())
            .paginate(page=page, per_page=per_page)
        )
        if not results:
            raise NotFound("Comments not found!")

        comments = CommentReadList(
            comment_tree=[CommentTree.model_validate(result) for result in results],
            pagination=Pagination(
                total=results.total,
                page=results.page,
                per_page=results.per_page,
                pages=results.pages,
            ),
        )
        current_app.logger.info(
            f"View child comments of comment {comment_id} successfully."
        )
        return api_response(
            data=comments.model_dump(),
            message="View child comments successfully.",
            status=200,
        )


@postRoute.route("/<int:post_id>/comments", methods=["POST"])
@postRoute.route("/<int:post_id>/comments/<int:comment_id>", methods=["POST"])
@token_required
@limiter.limit(
    "30/hour",
    key_func=user_id_from_token_key,
    error_message="Too many comment on post attempts. Please try again later.",
)
def comment_on_post(post_id: int, current_user: User, comment_id: int = None):
    json_data = request.get_json()

    content = json_data.get("content").strip()
    if not content:
        raise BadRequest("Comment content cannot be empty.")
    if len(content) > 100:
        raise BadRequest("Comment is too long.")

    with db_session() as session:
        post = session.query(Post).where(Post.id == post_id).first()
        if not post:
            raise NotFound(f"Post {post_id} not found!")

        comment_to_add = {
            "post_id": post_id,
            "user_id": current_user.id,
            "content": content,
        }
        if comment_id:
            comment_to_add["parent_comment_id"] = comment_id
        comment = Comment(**comment_to_add)
        session.add(comment)
        session.commit()

        current_app.logger.info(f"Comment on post {post_id} successfully.")
        return api_response(message="Comment added successfully!")


@postRoute.route("/<int:post_id>/comments/<int:comment_id>", methods=["PUT"])
@token_required
@limiter.limit(
    "30/hour",
    key_func=user_id_from_token_key,
    error_message="Too many update comment attempts. Please try again later.",
)
def update_comment(post_id: int, current_user: User, comment_id: int = None):

    json_data = request.get_json()

    content = json_data.get("content").strip()
    if not content:
        raise BadRequest("Comment content cannot be empty.")
    if len(content) > 100:
        raise BadRequest("Comment is too long.")

    with db_session() as session:
        post = session.query(Post).where(Post.id == post_id).first()
        if not post:
            raise NotFound(f"Post {post_id} not found!")
        comment = session.query(Comment).where(Comment.id == comment_id).first()
        if not comment:
            raise NotFound(f"Comment {comment_id} not found!")
        if post.user_id != current_user.id:
            raise Forbidden("You are not authorized to update this comment!")
        #   Update comment
        comment.content = content
        session.commit()
        return api_response(message="Update comment successfully.")


@postRoute.route("/<int:post_id>/comments/<int:comment_id>", methods=["DELETE"])
@token_required
@limiter.limit(
    "30/hour",
    key_func=user_id_from_token_key,
    error_message="Too many delete comment attempts. Please try again later.",
)
def delete_comment_from_post(post_id: int, comment_id: int, current_user: User):

    with db_session() as session:
        post = session.query(Post).where(Post.id == post_id).first()
        if not post:
            raise NotFound(f"Post {post_id} not found!")
        if post.user_id != current_user.id:
            raise Forbidden("You are not authorized to delete this comment!")
        comment = session.query(Comment).where(Comment.id == comment_id).first()
        if not comment:
            raise NotFound(f"Comment {comment_id} not found!")
        #   Delete comment
        session.delete(comment)
        session.commit()
        current_app.logger.info(f"Delete comment {comment_id} successfully.")
        return api_response(message="Delete comment successfully.")


@postRoute.route("/search", methods=["GET"])
@token_required
@limiter.limit(
    "10/minute",
    key_func=user_id_from_token_key,
    error_message="Too many search post attempts. Please try again later.",
)
def search_post(current_user: User):
    tag = request.args.get("tag", "", type=str)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    with db_session() as session:
        posts = (
            session.query(Post)
            .join(PostTag, Post.id == PostTag.post_id)
            .join(Tag, Tag.id == PostTag.tag_id)
            .filter(Tag.tag_name == tag)
            .order_by(Post.created_at.desc())
            .paginate(page=page, per_page=per_page)
        )

        posts_by_tag = PostReadList(
            posts=[
                post.to_dict(
                    current_user=current_user,
                    include_user=True,
                    include_like=True,
                    include_comment=True,
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
        current_app.logger.info(f"Search post by tag {tag} successfully.")
        return api_response(
            data=posts_by_tag.model_dump(),
            message=f"Search post by tag {tag} successfully.",
            status=200,
        )
