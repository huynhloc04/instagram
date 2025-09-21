#!/usr/bin/env python3
"""
Celery worker entry point for Instagram backend.
Configured with Flask app context for template rendering.
"""

from app.v1 import create_app
from app.core.celery import celery, init_celery

# Create Flask app and configure Celery with context
app = create_app()
init_celery(app)
