import json
import logging
from datetime import datetime, timezone
from typing import Any

from rich.logging import RichHandler


def setup_logger(name: str = "ai_data_qa") -> logging.Logger:
    """Sets up structured logger with Rich output."""
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    logger_obj = logging.getLogger(name)
    return logger_obj


def log_event(event: str, level: int = logging.INFO, **context: Any) -> None:
    """Log an event as JSON for consistent machine-readable diagnostics."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **context,
    }
    logger.log(level, json.dumps(payload, default=str))


logger = setup_logger()
