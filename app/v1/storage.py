#   References: https://github.com/faizan170/google-cloud-storage-flask

import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound, InternalServerError

from app.core.config import settings
from app.v1.utils import get_gcs_client


client = get_gcs_client()
bucket = client.bucket(settings.BUCKET_NAME)


def gcs_upload(file_obj) -> str:
    """Uploads a file to the bucket."""
    try:
        sanitized_filename = secure_filename(file_obj.filename)
        unique_filename = f"{str(uuid.uuid4())}_{sanitized_filename}"
        gcs_filename = os.path.join(settings.POST_BUCKET_FOLDER, unique_filename)

        blob = bucket.blob(gcs_filename)
        blob.upload_from_file(file_obj, content_type=file_obj.content_type)

        current_app.logger.debug(
            f"File {file_obj.filename} uploaded to {settings.POST_BUCKET_FOLDER}/."
        )
        return unique_filename
    except Exception as error:
        raise InternalServerError(f"Error saving image: {error}.")


def gcs_delete(filename: str) -> None:
    """Deletes a blob from the bucket."""
    try:
        blob = bucket.blob(filename)
        if not blob.exists():
            raise NotFound(f"File {filename} not found!")

        blob.delete()
        return True
    except Exception as error:
        raise InternalServerError(f"Error deleting image: {error}.")
