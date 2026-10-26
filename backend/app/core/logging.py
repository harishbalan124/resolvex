import logging
import re
import sys
from typing import Any

# Patterns to mask sensitive data
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_REGEX = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
CREDIT_CARD_REGEX = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')


def mask_sensitive_data(message: str) -> str:
    """Mask email, phone numbers, and card numbers to prevent PII leaks."""
    if not isinstance(message, str):
        message = str(message)
    message = CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", message)
    message = EMAIL_REGEX.sub("[REDACTED_EMAIL]", message)
    message = PHONE_REGEX.sub("[REDACTED_PHONE]", message)
    return message


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: mask_sensitive_data(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(mask_sensitive_data(str(arg)) for arg in record.args)
        return True


def setup_logging():
    logger = logging.getLogger("resolvex")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())
    logger.addHandler(handler)
    return logger


logger = setup_logging()
