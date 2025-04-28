"""Logging configuration for the application."""

import json
import logging
import sys
from typing import Any

from app.core.config import settings


class JsonFormatter(logging.Formatter):
    """Formatter for outputting logs in JSON format for CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON formatted log string.
        """
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
        }

        # Add exception info if it exists
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "id",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            }:
                log_record[key] = value

        return json.dumps(log_record)


def setup_logging() -> None:
    """Configure application logging.

    Sets up JSON formatting for logs in production and standard formatting in development.
    """
    root_logger = logging.getLogger()

    # Clear existing handlers to ensure we don't duplicate log output
    root_logger.handlers = []

    # Set log level based on environment
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Create handler for stdout
    stdout_handler = logging.StreamHandler(sys.stdout)

    # Use JSON formatter in production, more human-readable format in development
    if settings.DEBUG:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = JsonFormatter()

    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)

    # Configure file handler for app.log (which CloudWatch will monitor)
    try:
        file_handler = logging.FileHandler("/app/logs/app.log")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except (OSError, PermissionError):
        logging.warning(
            "Unable to set up file logging to /app/logs/app.log. Continuing with stdout only."
        )

    # Set propagate=False for some noisy third-party loggers to reduce log volume
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(logger_name).propagate = False

    # Log startup information
    logging.info(f"Logging initialized: {'DEBUG' if settings.DEBUG else 'PRODUCTION'} mode")
