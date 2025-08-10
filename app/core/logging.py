import os
import sys
from logging.config import dictConfig

from app.core.config import settings
from app.core.json_logging import JsonFormatter

LOG_LEVEL = settings.log_level


def get_logging_config() -> dict:
    """
    Generate logging configuration based on settings.
    Falls back to console-only logging if file logging is disabled or fails.
    Includes configuration for uvicorn access logs to ensure request_id correlation.
    """
    handlers: list[str] = ["console"]

    # Configure handlers
    config_handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": sys.stdout,
        }
    }

    if settings.enable_file_logging:
        config_handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": settings.log_file_path,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
        }
        handlers.append("file")

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            },
            "json": {
                "()": JsonFormatter,
                "application": "cliporaai-backend",
                "environment": settings.environment,
            },
            "access_json": {
                "()": JsonFormatter,
                "application": "cliporaai-backend",
                "environment": settings.environment,
                "log_type": "access",
            },
        },
        "handlers": config_handlers,
        "loggers": {
            "uvicorn": {
                "handlers": handlers,
                "level": LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": handlers,
                "level": LOG_LEVEL,
                "propagate": False,
                "formatter": "access_json",
            },
        },
        "root": {
            "handlers": handlers,
            "level": LOG_LEVEL,
        },
    }


def setup_logging() -> None:
    """
    Set up logging configuration with error handling.
    Falls back to console-only logging if file logging fails.
    """
    if settings.enable_file_logging:
        try:
            # Get the directory from the log file path
            log_file_path = settings.log_file_path
            if not os.path.isabs(log_file_path):
                # If it's a relative path, make it absolute from the project root
                log_file_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    log_file_path,
                )

            log_dir = os.path.dirname(log_file_path)
            os.makedirs(log_dir, exist_ok=True)

            with open(log_file_path, "a"):
                pass

        except (OSError, PermissionError) as e:
            print(f"Warning: Could not access log file: {e}")
            print("Falling back to console-only logging")
            # Disable file logging if there's an error
            settings.enable_file_logging = False

    logging_config = get_logging_config()
    dictConfig(logging_config)
