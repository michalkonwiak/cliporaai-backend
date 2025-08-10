import json
import logging
import traceback
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the log record.
    
    Usage:
        json_formatter = JsonFormatter()
        json_handler = logging.StreamHandler()
        json_handler.setFormatter(json_formatter)
        logger.addHandler(json_handler)
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the formatter with specified JSON attributes."""
        self.json_attributes = kwargs

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.name == "uvicorn.access":
            if hasattr(record, "scope"):
                scope = record.scope
                if "headers" in scope:
                    headers = dict([(k.decode('utf-8'), v.decode('utf-8'))
                                    for k, v in scope["headers"]])
                    request_id = headers.get("x-request-id")
                    if request_id:
                        log_data["request_id"] = request_id

                log_data.update({
                    "method": scope.get("method", ""),
                    "path": scope.get("path", ""),
                    "client": scope.get("client", ("", 0))[0],
                    "http_version": scope.get("http_version", ""),
                })

            if hasattr(record, "status_code"):
                log_data["status_code"] = record.status_code
            if hasattr(record, "response_time"):
                log_data["response_time_ms"] = round(record.response_time * 1000, 2)

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        log_data.update(self.json_attributes)

        if record.exc_info and record.exc_info[0] is not None:
            exc_type, exc_value, exc_traceback = record.exc_info
            log_data["exception"] = {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback)
            }

        # Add any extra attributes set on the record
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_json_logging(logger: logging.Logger | None = None) -> None:
    """
    Set up JSON logging for the specified logger or the root logger.
    
    Args:
        logger: The logger to set up JSON logging for. If None, the root logger is used.
    """
    if logger is None:
        logger = logging.getLogger()

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    logger.setLevel(logging.INFO)
