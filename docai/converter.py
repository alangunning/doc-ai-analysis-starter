"""Unified document conversion helpers.

Provides a thin wrapper around the current conversion backend (Docling)
so callers can request various output formats without depending on the
underlying library.  The interface is intentionally small to allow
future backends to be swapped in without touching calling code.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, Union

from docling.document_converter import DocumentConverter as _DoclingConverter

# Supported high level output formats.
class OutputFormat(str, Enum):
    """Canonical output formats supported by the converter."""

    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    TEXT = "text"
    DOCTAGS = "doctags"


# Map output formats to the method on the Docling Document object
# that renders that representation.
_METHOD_MAP: Dict[OutputFormat, str] = {
    OutputFormat.MARKDOWN: "as_markdown",
    OutputFormat.HTML: "as_html",
    OutputFormat.JSON: "as_json",
    OutputFormat.TEXT: "as_text",
    OutputFormat.DOCTAGS: "as_doctags",
}

# File extension for each format so callers can write outputs with a
# predictable suffix.
_SUFFIX_MAP: Dict[OutputFormat, str] = {
    OutputFormat.MARKDOWN: ".md",
    OutputFormat.HTML: ".html",
    OutputFormat.JSON: ".json",
    OutputFormat.TEXT: ".txt",
    OutputFormat.DOCTAGS: ".doctags",
}


def convert_file(input_path: Path, output_path: Path, fmt: OutputFormat) -> None:
    """Convert a document to the requested format and write it to ``output_path``.

    Parameters
    ----------
    input_path: Path
        The path of the source document.
    output_path: Path
        Where to write the converted content.
    fmt: OutputFormat
        Desired output format.
    """

    converter = _DoclingConverter()
    document = converter.convert(input_path)
    render_method = getattr(document, _METHOD_MAP[fmt])
    content: Union[str, bytes] = render_method()

    if isinstance(content, bytes):
        output_path.write_bytes(content)
    else:
        output_path.write_text(content, encoding="utf-8")


def suffix_for_format(fmt: OutputFormat) -> str:
    """Return the default file suffix for ``fmt``."""

    return _SUFFIX_MAP[fmt]


__all__ = ["OutputFormat", "convert_file", "suffix_for_format"]
