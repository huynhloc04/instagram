from celery import Celery

def create_celery(settings) -> Celery:
    celery = Celery(__name__)

    celery.conf.update(
        broker_url=settings.CELERY_BROKER_URL,
        result_backend=settings.CELERY_RESULT_BACKEND,
        include=["app.v1.tasks"],
        task_acks_late=True,
        task_acks_on_failure_or_timeout=True,
        broker_transport_options={
            "visibility_timeout": 120
        },
    )

    return celery


def init_celery_worker(celery: Celery, app) -> Celery:
    """
    Initialize Celery with Flask app context.
    """

    # Update task base classes to use Flask app context
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
