import logging
import os
import config

LOG_FILE = os.path.join(config.get_data_dir(), "app.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def get_logger(name):
    return logging.getLogger(name)
