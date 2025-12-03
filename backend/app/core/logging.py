# backend/app/core/logging.py
"""
Logging configuration using Loguru with best practices.
"""
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import Logger

# Constants
LOG_ROTATION_SIZE = "10 MB"

# Remove default logger
logger.remove()

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Console logging with colors and formatting
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)

# File logging - General logs (rotation)
logger.add(
    LOGS_DIR / "app.log",
    rotation=LOG_ROTATION_SIZE,  # Rotate when file reaches 10MB
    retention="7 days",  # Keep logs for 7 days
    compression="zip",  # Compress rotated files
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
)

# File logging - Error logs only
logger.add(
    LOGS_DIR / "errors.log",
    rotation=LOG_ROTATION_SIZE,
    retention="30 days",  # Keep error logs longer
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    backtrace=True,
    diagnose=True,
)

# File logging - Access logs for API requests
logger.add(
    LOGS_DIR / "access.log",
    rotation=LOG_ROTATION_SIZE,
    retention="7 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
    level="INFO",
    filter=lambda record: "ACCESS" in record["extra"],
)


def get_logger(name: str = __name__) -> "Logger":
    """
    Get a logger instance with a specific name.

    Args:
        name: Logger name (usually __name__ from calling module)

    Returns:
        Configured logger instance
    """
    return logger.bind(name=name)


# Export logger for use in other modules
__all__ = ["logger", "get_logger"]
