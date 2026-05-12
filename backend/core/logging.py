"""
Structured logging configuration using Loguru.
Supports console and file logging with rotation.
"""
import sys
import logging
from pathlib import Path
from loguru import logger
from backend.core.config import settings


def setup_logging() -> None:
    """Configure application-wide logging."""
    # Remove default handler
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File handler - all logs (optional, try to create but fail gracefully)
    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        logger.add(
            log_dir / "app.log",
            format=log_format,
            level="INFO",
            rotation="10 MB",
            retention="30 days",
            compression="gz",
            backtrace=True,
            diagnose=False,
        )

        # File handler - errors only
        logger.add(
            log_dir / "error.log",
            format=log_format,
            level="ERROR",
            rotation="5 MB",
            retention="60 days",
            compression="gz",
            backtrace=True,
            diagnose=True,
        )
    except (PermissionError, OSError) as e:
        # If file logging fails (e.g., in Docker with permission issues), continue with console logging
        logger.warning(f"File logging disabled: {e}")

    # Intercept standard library logging
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back  # type: ignore
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logger.info(
        f"Logging configured | ENV={settings.APP_ENV} | DEBUG={settings.DEBUG}"
    )
