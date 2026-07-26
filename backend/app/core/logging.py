"""Stdlib logging configuration, applied once at app startup."""
import logging
import sys

from app.config import settings


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return  # already configured (e.g. re-imported under a test runner)

    root.setLevel(settings.log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    )
    root.addHandler(handler)

    # uvicorn's own loggers are configured separately by uvicorn itself;
    # leave them alone so request-access logs keep their own format.


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
