from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler

# Patterns that may expose sensitive information such as API keys or tokens
SENSITIVE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*[^\s]+"),
    re.compile(r"(?i)token\s*[:=]\s*[^\s]+"),
]


def _redact(text: str) -> str:
    """Redact sensitive substrings from the provided text."""
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


class RedactingFilter(logging.Filter):
    """Logging filter that redacts sensitive values from log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - trivial
        record.msg = _redact(str(record.msg))
        if record.args:
            record.args = tuple(_redact(str(a)) for a in record.args)
        return True


def setup_logging(level: str | int, log_file: Optional[Path | str] = None) -> logging.Logger:
    """Configure application logging.

    Parameters
    ----------
    level:
        Logging level for console output (e.g. "INFO", "DEBUG").
    log_file:
        Optional path to a log file. When provided, detailed debug logs are
        written to this file with sensitive fields redacted.
    """

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)

    redactor = RedactingFilter()
    level_value = getattr(logging, str(level).upper(), logging.INFO)

    console_handler = RichHandler(show_time=False)
    console_handler.setLevel(level_value)
    console_handler.addFilter(redactor)
    root.addHandler(console_handler)

    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        )
        file_handler.addFilter(redactor)
        root.addHandler(file_handler)

    return root
