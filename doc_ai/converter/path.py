from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Tuple
from urllib.parse import urlparse
from tempfile import TemporaryDirectory

from docling.exceptions import ConversionError

from .document_converter import OutputFormat, convert_files, suffix_for_format
from doc_ai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)

from ..utils import http_get, sanitize_path

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


def convert_path(
    source: Path | str, formats: Iterable[OutputFormat]
) -> Dict[Path, Tuple[Dict[OutputFormat, Path], Any]]:
    """Convert a file or all files under a directory in-place.

    ``source`` may be a filesystem path or an HTTP(S) URL to a single file.

    Returns a mapping of each processed file to a tuple containing the
    format-to-path mapping written for that file and Docling's
    ``ConversionStatus``.
    """

    source_url: str | None = None

    def _process(src: Path, src_url: str | None = None) -> Dict[Path, Tuple[Dict[OutputFormat, Path], Any]]:
        fmt_list = list(formats)
        output_suffixes = {_suffix(fmt) for fmt in OutputFormat}
        results: Dict[Path, Tuple[Dict[OutputFormat, Path], Any]] = {}

        def is_output_file(path: Path) -> bool:
            name = path.name.lower()
            if name.endswith(".metadata.json"):
                return True
            return any(name.endswith(suf) for suf in output_suffixes)

        def handle_file(file: Path, src_url: str | None = None) -> None:
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
                for fmt in fmt_list
                if not (fmt == OutputFormat.MARKDOWN and file.suffix.lower() == ".md")
            }
            inputs = {"source": str(file), "formats": [fmt.value for fmt in fmt_list]}
            if src_url is not None:
                inputs["source_url"] = src_url
            if not outputs:
                mark_step(meta, "conversion", inputs=inputs)
                save_metadata(file, meta)
                return
            try:
                written, status = convert_files(file, outputs, return_status=True)
            except ConversionError:
                return
            results[file] = (written, status)
            mark_step(
                meta,
                "conversion",
                outputs=[str(p.name) for p in outputs.values()],
                inputs=inputs,
            )
            save_metadata(file, meta)

        if src.is_file():
            handle_file(src, src_url)
        else:
            for file in src.rglob("*"):
                if file.is_file():
                    handle_file(file)

        return results

    if isinstance(source, str):
        if source.startswith(("http://", "https://")):
            source_url = source
            with TemporaryDirectory() as tmp:
                resp = http_get(source)
                resp.raise_for_status()
                name = Path(urlparse(source).path).name or "downloaded"
                source_path = Path(tmp) / name
                source_path.write_bytes(resp.content)
                return _process(source_path, source_url)
        source_path = sanitize_path(source)
    else:
        source_path = sanitize_path(source)
    return _process(source_path, source_url)
