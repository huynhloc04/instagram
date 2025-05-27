import uuid
import os

from werkzeug.utils import secure_filename
from flask import current_app
from sqlalchemy.orm import Session
from werkzeug.exceptions import InternalServerError

from app.core.config import settings
from app.v1.models.post import Post
from app.v1.schemas.post import PostCreate, PostEdit


def handle_upload_image(image) -> str:
    sanitized_filename = secure_filename(image.filename)
    unique_filename = f"{str(uuid.uuid4())}_{sanitized_filename}"
    try:
        #   TODO: Upload to Cloud service instead
        image.save(
            os.path.join("static/uploads", unique_filename)
        )
        current_app.logger.info("Image uploaded successfully.")
        return unique_filename
    except Exception as error:
        raise InternalServerError(f"Error saving image: {error}.")

def create_post(data: PostCreate, session: Session) -> Post:
    post = Post(**data.dict())
    session.add(post)
    session.flush()
    return post

def update_post(post: Post, data: PostEdit, session: Session) -> None:
    for field_to_update, value in data.dict(
        exclude_unset=True, exclude_none=True
    ).items():
        setattr(post, field_to_update, value)
    return post