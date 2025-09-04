"""Logging utilities with Rich formatting and redaction."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable

from rich.logging import RichHandler


# Patterns that likely represent API keys or tokens that should be redacted
_SECRET_PATTERNS: list[re.Pattern[str]] = [
    # OpenAI style keys: ``sk-`` followed by 16+ base64-like chars
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    # GitHub personal access tokens: ``ghp_``/``gho_``/``ghs_``/``ghr_`` with 36+ chars
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    # GitHub fine-grained tokens begin with ``github_pat_`` and are long
    re.compile(r"github_pat_[A-Za-z0-9_]{80,}"),
]


class RedactFilter(logging.Filter):
    """Filter that redacts known secret patterns from log records."""

    def __init__(self, patterns: Iterable[re.Pattern[str]] | None = None) -> None:
        super().__init__()
        self.patterns = list(patterns or _SECRET_PATTERNS)

    def _redact(self, value: str) -> str:
        for pat in self.patterns:
            value = pat.sub("<redacted>", value)
        return value

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - exercised via tests
        if isinstance(record.msg, str):
            record.msg = self._redact(record.msg)
        if record.args:
            record.args = tuple(
                self._redact(arg) if isinstance(arg, str) else arg for arg in record.args
            )
        return True


def configure_logging(level: str | int = "WARNING", log_file: str | Path | None = None) -> None:
    """Configure application logging with rich formatting and optional file output."""

    if isinstance(level, str):
        numeric_level = logging.getLevelName(level.upper())
        if isinstance(numeric_level, str):  # logging returns 'Level X'
            numeric_level = logging.WARNING
    else:
        numeric_level = level

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(numeric_level)

    redact_filter = RedactFilter()

    console_handler = RichHandler(rich_tracebacks=True, markup=True)
    console_handler.setLevel(numeric_level)
    console_handler.addFilter(redact_filter)
    root.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        )
        file_handler.addFilter(redact_filter)
        root.addHandler(file_handler)

    logging.captureWarnings(True)
    pywarn = logging.getLogger("py.warnings")
    if numeric_level <= logging.DEBUG:
        pywarn.setLevel(logging.WARNING)
    else:
        pywarn.setLevel(logging.ERROR)


__all__ = ["configure_logging", "RedactFilter"]
