import uuid
import os

from werkzeug.utils import secure_filename
from flask import current_app
from sqlalchemy.orm import Session
from werkzeug.exceptions import InternalServerError
from sqlalchemy import text

from app.v1.models.post import Post
from app.v1.models import Tag, PostTag, Post, Follow
from app.v1.schemas.post import PostCreate, PostEdit, FollowUser


def handle_upload_image(image) -> str:
    sanitized_filename = secure_filename(image.filename)
    unique_filename = f"{str(uuid.uuid4())}_{sanitized_filename}"
    try:
        #   TODO: Upload to Cloud service instead
        image.save(os.path.join("static/uploads", unique_filename))
        current_app.logger.info("Image uploaded successfully.")
        return unique_filename
    except Exception as error:
        raise InternalServerError(f"Error saving image: {error}.")


def create_post(data: PostCreate, session: Session) -> Post:
    post = Post(**data.model_dump())
    session.add(post)
    session.flush()
    return post


def update_post(post: Post, data: PostEdit) -> None:
    for field_to_update, value in data.model_dump(
        exclude_unset=True, exclude_none=True
    ).items():
        setattr(post, field_to_update, value)
    return post


def create_follow_user(data: FollowUser, session: Session) -> None:
    follow = Follow(**data.model_dump())
    session.add(follow)
    session.flush()


def get_list_followers(user_id: int):
    """
    SELECT * FROM users
    JOIN follows ON follows.follower_id=users.id
    WHERE follows.following_id=1
    """


def get_base_comment_and_count(post_id: int, session: Session):
    raw_sql = text(
        """
        WITH child_cte AS (
            SELECT 
                parent_comment_id,
                COUNT(*) AS reply_count
            FROM comments
            WHERE parent_comment_id IS NOT NULL
            GROUP BY parent_comment_id
        )
        SELECT 
            base.id,
            base.created_at,
            base.modified_at,
            base.content,
            base.user_id,
            base.post_id,
            base.parent_comment_id,
            COALESCE(child_cte.reply_count, 0) AS reply_count
        FROM comments AS base
        LEFT JOIN child_cte ON base.id = child_cte.parent_comment_id
        WHERE 
            base.parent_comment_id IS NULL 
        AND
            base.post_id = :post_id;
    """
    )

    result = session.execute(raw_sql, {"post_id": post_id})
    comments = result.fetchall()
    return [dict(row._mapping) for row in comments]


def extract_tags(caption: str) -> list[str]:
    """
    Extracts hashtags from a caption.

    Args:
        caption (str): The text of the post caption.

    Returns:
        List[str]: A list of extracted hashtags without the '#' symbol.
    """
    if not caption:
        return []

    # Regular expression to match hashtags (e.g. #sunset, #hello_world)
    return re.findall(r"#(\w+)", caption)


def create_tags(post: Post, session: Session):
    """
    1. Extract tags from post's caption
    2. Save tags to database
    3. Attach tags to post
    """
    extracted_tags = extract_tags(caption=post.caption)
    #   Fetch all existing tags
    existing_tags = session.query(Tag).where(Tag.tag_name.in_(extracted_tags)).all()
    existing_tag_names = {existing_tag.tag_name for existing_tag in existing_tags}
    #   Determine tags to create newly
    new_tag_names = set(extracted_tags) - existing_tag_names

    try:
        tags = [Tag(tag_name=tag_name) for tag_name in new_tag_names]
        session.add_all(tags)
        session.flush()
    except Exception as error:
        raise ValueError(f"Tags created error: {error}")

    try:
        tag_to_post = [*tags, *existing_tags]
        post_tags = [PostTag(tag_id=tag.id, post_id=post.id) for tag in tag_to_post]
        session.add_all(post_tags)
        session.flush()
    except Exception as error:
        raise ValueError(f"Attached tag to post {post.id} error: {error}")
