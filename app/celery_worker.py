"""
Celery worker entry point.
Used by: celery -A app.celery_worker.celery worker
"""

from app.core.celery import init_celery_worker
from app.main import create_app

# Create Flask app
app = create_app()
container = app.container

# Create Celery from DI
celery = container.celery_app()
init_celery_worker(celery, app)
