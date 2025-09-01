from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple, Dict, Optional, TYPE_CHECKING

from docling.exceptions import ConversionError

from .document_converter import OutputFormat, convert_files, suffix_for_format
from doc_ai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)

# File suffixes supported by Docling's ``DocumentConverter``.
# Anything not in this list will be skipped instead of raising an error when
# walking directories of mixed content.
SUPPORTED_SUFFIXES = {
    ".docx",
    ".pptx",
    ".html",
    ".htm",
    ".pdf",
    ".asciidoc",
    ".adoc",
    ".md",
    ".markdown",
    ".csv",
    ".xlsx",
    ".xml",
    ".json",
    # Common image formats
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
    ".svg",
    # Common audio formats
    ".wav",
    ".mp3",
    ".flac",
    ".m4a",
    ".ogg",
}


def _suffix(fmt: OutputFormat) -> str:
    """Return desired suffix for ``fmt``."""

    return f".converted{suffix_for_format(fmt)}"


if TYPE_CHECKING:  # pragma: no cover - typing only
    from docling.document_converter import ConversionStatus


def convert_path(
    source: Path,
    formats: Iterable[OutputFormat],
    *,
    return_results: bool = False,
) -> Optional[List[Tuple[Path, Dict[OutputFormat, Path], "ConversionStatus"]]]:
    """Convert a file or all files under a directory in-place.

    When ``return_results`` is ``True`` a list of tuples of the source file,
    written paths and Docling's ``ConversionStatus`` is returned.
    """

    output_suffixes = {_suffix(fmt) for fmt in OutputFormat}

    def is_output_file(path: Path) -> bool:
        name = path.name.lower()
        return any(name.endswith(suf) for suf in output_suffixes)

    results: List[Tuple[Path, Dict[OutputFormat, Path], "ConversionStatus"]] = []

    def handle_file(file: Path) -> None:
        """Convert ``file`` if it's not already a derived output and hasn't been processed."""

        if is_output_file(file):
            return
        if file.suffix.lower() not in SUPPORTED_SUFFIXES:
            return

        meta = load_metadata(file)
        file_hash = compute_hash(file)
        if meta.blake2b == file_hash and is_step_done(meta, "conversion"):
            return
        if meta.blake2b != file_hash:
            meta.blake2b = file_hash
            meta.extra = {}

        outputs = {
            fmt: file.with_name(file.name + _suffix(fmt))
            for fmt in formats
            if not (fmt == OutputFormat.MARKDOWN and file.suffix.lower() == ".md")
        }
        if not outputs:
            mark_step(meta, "conversion")
            save_metadata(file, meta)
            return
        try:
            result = convert_files(file, outputs, with_status=return_results)
        except ConversionError:
            return
        if return_results:
            written, status = result  # type: ignore[misc]
            results.append((file, written, status))
        mark_step(
            meta,
            "conversion",
            outputs=[str(p.name) for p in outputs.values()],
        )
        save_metadata(file, meta)

    if source.is_file():
        handle_file(source)
    else:
        for file in source.rglob("*"):
            if file.is_file():
                handle_file(file)

    if return_results:
        return results
    return None
