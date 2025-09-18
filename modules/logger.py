# modules/logger.py
import logging
import os

LOG_FILE = None

def setup(log_file_path="logs/fb-bot.log"):
    global LOG_FILE
    LOG_FILE = log_file_path
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8")
        ]
    )

def info(msg):
    logging.info(msg)

def warn(msg):
    logging.warning(msg)

def error(msg):
    logging.error(msg)

def exception(msg):
    logging.exception(msg)