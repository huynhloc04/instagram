import os
import logging
from logging.handlers import RotatingFileHandler

from prometheus_client import Counter, Histogram

#   ==================================================
#   =============== Prometheus Logging ===============
#   ==================================================

REQUEST_COUNT = Counter(
    "sydegram_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "sydegram_http_request_duration_seconds",
    "HTTP Request latency",
    ["method", "endpoint"],
)

'''
With this code:
- Knows nothing about Flask
- Knows nothing about services
- Just configures Python logging
=> Seperate of concerns
'''


def configure_logging(log_level: str = "INFO", log_file: str | None = None):
    log_dir = "app/logs"
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s"
    )

    # Create a rotating file handler (5MB per file, keep 5 files)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Log to console as well
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(console_handler)
