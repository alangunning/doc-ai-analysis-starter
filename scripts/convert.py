import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from docai import OutputFormat, convert_files, suffix_for_format
from docai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)

load_dotenv()


def _suffix(fmt: OutputFormat) -> str:
    """Return desired suffix for ``fmt``."""

    suf = suffix_for_format(fmt)
    if fmt == OutputFormat.MARKDOWN:
        return ".converted.md"
    return suf


def convert_path(source: Path, formats: list[OutputFormat]) -> None:
    """Convert a file or all files under a directory in-place."""

    output_suffixes = {_suffix(fmt) for fmt in OutputFormat}

    def is_output_file(path: Path) -> bool:
        name = path.name.lower()
        return any(name.endswith(suf) for suf in output_suffixes)

    def handle_file(file: Path) -> None:
        """Convert ``file`` if it's not already a derived output and hasn't been processed."""

        if is_output_file(file):
            return

        meta = load_metadata(file)
        file_hash = compute_hash(file)
        if meta.blake2b == file_hash and is_step_done(meta, "conversion"):
            return
        if meta.blake2b != file_hash:
            meta.blake2b = file_hash
            meta.extra = {}

        outputs = {
            fmt: file.with_suffix(_suffix(fmt))
            for fmt in formats
            if not (fmt == OutputFormat.MARKDOWN and file.suffix.lower() == ".md")
        }
        if not outputs:
            mark_step(meta, "conversion")
            save_metadata(file, meta)
            return
        convert_files(file, outputs)
        mark_step(meta, "conversion")
        save_metadata(file, meta)

    if source.is_file():
        handle_file(source)
    else:
        for file in source.rglob("*"):
            if file.is_file():
                handle_file(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Path to raw document or folder")
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        help="Desired output format(s). Can be passed multiple times.\n"
        "If omitted, the OUTPUT_FORMATS environment variable or Markdown is used.",
    )
    args = parser.parse_args()

    in_path = Path(args.source)

    def parse_formats(values: list[str]) -> list[OutputFormat]:
        formats: list[OutputFormat] = []
        for val in values:
            try:
                formats.append(OutputFormat(val.strip()))
            except ValueError as exc:  # provide clearer error message
                valid = ", ".join(f.value for f in OutputFormat)
                raise SystemExit(f"Invalid output format '{val}'. Choose from: {valid}") from exc
        return formats

    if args.formats:
        fmts = parse_formats(args.formats)
    elif os.getenv("OUTPUT_FORMATS"):
        fmts = parse_formats(os.getenv("OUTPUT_FORMATS").split(","))
    else:
        fmts = [OutputFormat.MARKDOWN]

    convert_path(in_path, fmts)
