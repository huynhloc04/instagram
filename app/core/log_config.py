import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    log_dir = "app/static/logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "app.log")

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    # Create a rotating file handler (5MB per file, keep 5 files)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Log to console as well
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    #   Set level for app handler
    app.logger.setLevel(logging.DEBUG)

