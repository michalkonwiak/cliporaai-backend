import os
import sys
from logging.config import dictConfig

from app.core.config import settings

LOG_LEVEL = settings.log_level

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": "logs/app.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
    },
}


def setup_logging() -> None:
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)
    dictConfig(LOGGING_CONFIG)
