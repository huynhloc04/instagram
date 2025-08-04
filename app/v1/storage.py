#   References: https://github.com/faizan170/google-cloud-storage-flask

import os
import uuid
import datetime
import mimetypes

from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound, InternalServerError
from google.cloud import storage

from app.core.config import settings


client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
bucket = client.bucket(settings.BUCKET_NAME)


def _get_content_type(filename: str) -> str:
    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        mime_type = "application/octet-stream"
    return mime_type


def _generate_put_singed_url(filename: str, expiration: int = 60) -> dict:
    """Uploads a file to the bucket."""
    try:
        #   Prepare filename
        sanitized_filename = secure_filename(filename)
        unique_filename = f"{str(uuid.uuid4())}_{sanitized_filename}"
        filename_path = os.path.join(settings.BUCKET_FOLDER, unique_filename)
        content_type = _get_content_type(filename)

        #   Get presign url
        blob = bucket.blob(filename_path)
        singed_url = blob.generate_signed_url(
            version="v4",
            method="PUT",
            expiration=datetime.timedelta(seconds=expiration),
            content_type=content_type,
        )

        return {
            "singed_url": singed_url,
            "filename": unique_filename,
            "expires_in": expiration,
            "content_type": content_type,
        }
    except Exception as error:
        raise InternalServerError(f"Error while getting presigned url: {error}.")


def _generate_get_singed_url(filename: str, expiration: int = 60) -> dict:
    """Uploads a file to the bucket."""
    try:
        filename_path = os.path.join(settings.BUCKET_FOLDER, filename)
        blob = bucket.blob(filename_path)
        singed_url = blob.generate_signed_url(
            version="v4",
            method="GET",
            expiration=datetime.timedelta(seconds=expiration),
            response_disposition="inline",  # Prevent download image
        )
        return {"singed_url": singed_url, "expires_in": expiration}
    except Exception as error:
        raise InternalServerError(f"Error while getting presigned url: {error}.")


def _storage_delete(filename: str) -> None:
    """Deletes a blob from the bucket."""
    try:
        blob = bucket.blob(filename)
        if not blob.exists():
            raise NotFound(f"File {filename} not found!")

        blob.delete()
        return True
    except Exception as error:
        raise InternalServerError(f"Error while deleting file: {error}.")
