import logging
from rich.logging import RichHandler

def setup_logger(name: str = "ai_data_qa") -> logging.Logger:
    """Sets up a structured logger using Rich."""
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    logger = logging.getLogger(name)
    return logger

logger = setup_logger()
