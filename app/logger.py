import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve configuration from environment variables or set defaults
app_name = os.getenv("APP_NAME", "default_app_name")
log_name = os.getenv("LOG_NAME", "default_log_name")
log_level = os.getenv("LOG_LEVEL", "INFO").upper()


def setup_logger(name=app_name, log_file=f"{log_name}.log", level=log_level):
    """
    Create a comprehensive logger with multiple handlers.

    Features:
    - Console output
    - File logging with rotation
    - Structured logging
    """
    # Ensure log directory exists (logs/ directory at the root)
    log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Log file path within the "logs" directory
    log_file = os.path.join(log_dir, log_file)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(
        getattr(logging, level, logging.INFO)
    )  # Default to INFO if invalid level

    # Clear any existing handlers
    logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # File Handler with Rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Create a logger instance
configured_logger = setup_logger()
