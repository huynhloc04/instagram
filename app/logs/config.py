import os
import time
import logging
from logging.handlers import RotatingFileHandler

from flask import request
from prometheus_client import Counter, Gauge, Histogram, Summary


REQUEST_COUNT = Counter(
    'sydegram_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'sydegram_http_request_duration_seconds',
    'HTTP Request latency',
    ['method', 'endpoint']
)


def init_logging(app):
    log_dir = "app/logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "app.log")

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    # Create a rotating file handler (5MB per file, keep 5 files)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Log to console as well
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    #   Set level for app handler
    app.logger.setLevel(logging.DEBUG)


def setup_prometheus(app):
    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def record_metrics(response):
        latency = time.time() - request.start_time
        REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, request.path).observe(latency)
        return response