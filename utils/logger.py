"""
Logging Module

Provides centralized logging configuration for the entire system.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "30 days"
) -> logger:
    """
    Set up the application logger.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (if None, uses default)
        rotation: Log rotation size/time
        retention: How long to keep old logs

    Returns:
        Configured logger instance
    """
    # Remove default handler
    logger.remove()

    # Add console handler with color
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # Add file handler
    if log_file is None:
        log_file = Path("logs") / "job_system_{time:YYYY-MM-DD}.log"

    # Ensure log directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation=rotation,
        retention=retention,
        compression="zip"
    )

    logger.info(f"Logger initialized with level: {log_level}")

    return logger


# Create a default logger instance
app_logger = logger
