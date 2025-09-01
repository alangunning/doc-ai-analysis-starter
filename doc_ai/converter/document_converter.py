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
import json
from contextlib import nullcontext

from rich.console import Console

# ``Docling`` pulls in heavy dependencies like ``torch`` which can slow down
# startup considerably.  Import the converter lazily so simply importing this
# module doesn't trigger those imports.  Tests patch ``_DoclingConverter`` so we
# keep a module level reference that can be swapped out.  The instantiated
# converter is cached to avoid repeated heavy initialisation during a single
# process run.  A sentinel file in ``~/.cache/doc_ai`` records that the converter
# has been loaded once so subsequent *local* runs can skip the progress message.
_DoclingConverter = None
_converter_instance = None
_CACHE_MARKER = Path.home() / ".cache" / "doc_ai" / "docling_ready"
_console = Console()


def _get_docling_converter():
    """Return a cached instance of Docling's ``DocumentConverter``."""

    global _DoclingConverter, _converter_instance
    if _converter_instance is not None:
        return _converter_instance

    show_status = not _CACHE_MARKER.exists()
    status = (
        _console.status("Loading Docling (first run may download models)...")
        if show_status
        else nullcontext()
    )
    with status:  # pragma: no cover - visual progress only
        if _DoclingConverter is None:
            from docling.document_converter import (  # type: ignore
                DocumentConverter as _Docling,  # pylint: disable=C0415
            )
            _DoclingConverter = _Docling
        _converter_instance = _DoclingConverter()
    if show_status:
        _CACHE_MARKER.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_MARKER.touch()
    return _converter_instance

# Supported high level output formats.
class OutputFormat(str, Enum):
    """Canonical output formats supported by the converter."""

    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    TEXT = "text"
    DOCTAGS = "doctags"


# Map output formats to the method on the Docling ``DoclingDocument``
# that renders that representation.  Docling changed its API to expose
# ``export_to_*`` helpers instead of ``as_*`` methods, so adapt to the new
# names here.
_METHOD_MAP: Dict[OutputFormat, str] = {
    OutputFormat.MARKDOWN: "export_to_markdown",
    OutputFormat.HTML: "export_to_html",
    OutputFormat.TEXT: "export_to_text",
    OutputFormat.DOCTAGS: "export_to_doctags",
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


def convert_files(
    input_path: Path, outputs: Dict[OutputFormat, Path]
) -> Dict[OutputFormat, Path]:
    """Convert ``input_path`` to multiple formats.

    ``outputs`` maps each desired ``OutputFormat`` to the file path where the
    rendered content should be written.  The source document is converted only
    once, and the requested representations are emitted to their respective
    destinations.  The mapping of formats to the paths that were written is
    returned for convenience.
    """

    converter = _get_docling_converter()
    result = converter.convert(input_path)
    doc = result.document

    written: Dict[OutputFormat, Path] = {}
    for fmt, out_path in outputs.items():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == OutputFormat.JSON:
            # ``DoclingDocument`` doesn't expose an explicit JSON exporter; use
            # the dictionary representation and serialize it ourselves.
            content: Union[str, bytes] = json.dumps(
                doc.export_to_dict(), ensure_ascii=False
            )
        else:
            render_method = getattr(doc, _METHOD_MAP[fmt])
            content = render_method()
        if isinstance(content, bytes):
            out_path.write_bytes(content)
        else:
            out_path.write_text(content, encoding="utf-8")
        written[fmt] = out_path

    return written


def convert_file(input_path: Path, output_path: Path, fmt: OutputFormat) -> Path:
    """Convert ``input_path`` to a single ``fmt`` and return the written path."""

    return convert_files(input_path, {fmt: output_path})[fmt]


def suffix_for_format(fmt: OutputFormat) -> str:
    """Return the default file suffix for ``fmt``."""

    return _SUFFIX_MAP[fmt]


__all__ = ["OutputFormat", "convert_files", "convert_file", "suffix_for_format"]
