import sys
import logging
import os
from logging.handlers import RotatingFileHandler
from app.core.config import settings

# Ensure logs directory exists
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Map string level to logging constant
LOG_LEVEL_MAP = {
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}

level = LOG_LEVEL_MAP.get(settings.LOG_LEVEL.upper(), logging.INFO)

# Formatter similar to SCTL: [TIMESTAMP] [LEVEL] MESSAGE
# Date fmt: YYYY-MM-DD HH:mm:ss
formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 1. Console Handler (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(level)

# 2. File Handler (Rotating)
# Max 10MB per file, keep 5 backups
file_handler = RotatingFileHandler(
    filename=os.path.join(LOGS_DIR, "sentinel.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)
file_handler.setLevel(level)

# Setup Root Logger
logger = logging.getLogger("sentinel")
logger.setLevel(level)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Prevent propagation if used inside other apps (though here it's main)
logger.propagate = False

# Silence SQLAlchemy Engine logs (too verbose usually)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def get_logger(name: str = None):
    if name:
        return logger.getChild(name)
    return logger
