import os
from sqlalchemy import delete

from app.core.config import settings
from app.v1.models import ImageCron
from app.v1.enums import ImageCronEnum
from app.v1.storage import gcs_delete
from app.core.database import db_session


def scheduler_delete_image(app):
    """
        Delete all unused image uploaded by users
        - Delete in Database: ImageCron table.
        - Delete on Google Cloud Storage.
    """
    with app.app_context():

        with db_session() as session:
            image_names = session.query(ImageCron.image_name)  \
                .filter(ImageCron.status==ImageCronEnum.unused.value).all()
            
            # Get IDs or names of successfully deleted images
            deleted_image_names = []

            #   Delete on the Google Cloud Storage
            for image_name in image_names:
                gcs_filename = os.path.join(settings.POST_BUCKET_FOLDER, image_name[0])
                gcs_delete(gcs_filename)
                deleted_image_names.append(image_name[0])

            #   Delete in Database (Only delete images that have been successfully deleted on GCS)
            if deleted_image_names:
                statement = delete(ImageCron)   \
                    .where(ImageCron.image_name.in_(deleted_image_names))
                session.execute(statement)
                session.commit()
