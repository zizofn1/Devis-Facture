import logging
from logging.handlers import RotatingFileHandler
import os
import config

LOG_FILE = os.path.join(config.get_data_dir(), "app.log")

# Setup RotatingFileHandler (max 1MB, keep 3 backups)
handler = RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024, backupCount=3, encoding="utf-8")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# Clear existing handlers to prevent duplicate logs if reloaded
if root_logger.hasHandlers():
    root_logger.handlers.clear()
root_logger.addHandler(handler)

def get_logger(name):
    return logging.getLogger(name)
