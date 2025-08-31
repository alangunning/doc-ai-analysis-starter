"""CLI orchestrator for AI document analysis pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import os

import typer
from rich.console import Console
from dotenv import load_dotenv

from doc_ai import OutputFormat, convert_files, suffix_for_format
from doc_ai.github import build_vector_store, run_prompt, validate_file
from doc_ai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)
from docling.exceptions import ConversionError

load_dotenv()

console = Console()
app = typer.Typer(
    help="Orchestrate conversion, validation, analysis and embedding generation."
)

ASCII_ART = r"""
    _____   ____   _____            _____    _____ _      _____
   |  __ \ / __ \ / ____|     /\   |_   _|  / ____| |    |_   _|
   | |  | | |  | | |        /  \    | |   | |    | |      | |
   | |  | | |  | | |       / /\ \   | |   | |    | |      | |
   | |__| | |__| | |____  / ____ \ _| |_  | |____| |____ _| |_
   |_____/ \____/ \_____|/_/    \_\_____|  \_____|______|_____|
"""

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
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
    ".svg",
    ".wav",
    ".mp3",
    ".flac",
    ".m4a",
    ".ogg",
}


def _suffix(fmt: OutputFormat) -> str:
    return f".converted{suffix_for_format(fmt)}"


def _parse_env_formats() -> List[OutputFormat] | None:
    """Return formats from OUTPUT_FORMATS env var if set."""

    env_val = os.getenv("OUTPUT_FORMATS")
    if not env_val:
        return None
    formats: List[OutputFormat] = []
    for val in env_val.split(","):
        try:
            formats.append(OutputFormat(val.strip()))
        except ValueError as exc:
            valid = ", ".join(f.value for f in OutputFormat)
            raise typer.BadParameter(
                f"Invalid output format '{val}'. Choose from: {valid}"
            ) from exc
    return formats


def convert_path(source: Path, formats: List[OutputFormat]) -> None:
    output_suffixes = {_suffix(fmt) for fmt in OutputFormat}

    def is_output_file(path: Path) -> bool:
        name = path.name.lower()
        return any(name.endswith(suf) for suf in output_suffixes)

    def handle_file(file: Path) -> None:
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
            convert_files(file, outputs)
        except ConversionError:
            return
        mark_step(meta, "conversion")
        save_metadata(file, meta)

    if source.is_file():
        handle_file(source)
    else:
        for file in source.rglob("*"):
            if file.is_file():
                handle_file(file)


def validate_doc(
    raw: Path,
    rendered: Path,
    fmt: OutputFormat | None = None,
    prompt: Path = Path("prompts/validate-output.prompt.yaml"),
    model: str | None = None,
    base_url: str | None = None,
) -> None:
    meta = load_metadata(raw)
    file_hash = compute_hash(raw)
    if meta.blake2b == file_hash and is_step_done(meta, "validation"):
        return
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}
    if fmt is None:
        mapping = {
            ".md": OutputFormat.MARKDOWN,
            ".html": OutputFormat.HTML,
            ".json": OutputFormat.JSON,
            ".txt": OutputFormat.TEXT,
            ".doctags": OutputFormat.DOCTAGS,
        }
        fmt = mapping.get(rendered.suffix)
        if fmt is None:
            valid = ", ".join(mapping.keys())
            raise typer.BadParameter(
                f"Unknown file extension '{rendered.suffix}'. Expected one of: {valid}"
            )
    verdict = validate_file(
        raw,
        rendered,
        fmt,
        prompt,
        model=model,
        base_url=base_url,
    )
    if not verdict.get("match", False):
        raise RuntimeError(f"Mismatch detected: {verdict}")
    mark_step(meta, "validation")
    save_metadata(raw, meta)


def analyze_doc(
    prompt: Path,
    markdown_doc: Path,
    output: Path | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> None:
    prompt_name = prompt.name.replace(".prompt.yaml", "")
    step_name = "analysis"
    meta = load_metadata(markdown_doc)
    file_hash = compute_hash(markdown_doc)
    if meta.blake2b == file_hash and is_step_done(meta, step_name):
        return
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}
    result = run_prompt(
        prompt,
        markdown_doc.read_text(),
        model=model,
        base_url=base_url,
    )
    out_path = (
        output if output else markdown_doc.with_suffix(f".{prompt_name}.json")
    )
    out_path.write_text(result + "\n", encoding="utf-8")
    mark_step(meta, step_name)
    save_metadata(markdown_doc, meta)


@app.callback()
def show_banner() -> None:  # pragma: no cover - visual flair only
    console.print(f"[bold green]{ASCII_ART}[/bold green]")


@app.command()
def convert(
    source: Path = typer.Argument(..., help="Path to raw document or folder"),
    format: List[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s). Can be passed multiple times.",
    ),
) -> None:
    """Convert files using Docling."""
    env_fmts = _parse_env_formats()
    fmts = format or env_fmts or [OutputFormat.MARKDOWN]
    convert_path(source, fmts)


@app.command()
def validate(
    raw: Path = typer.Argument(..., help="Path to raw document"),
    rendered: Path = typer.Argument(..., help="Path to converted file"),
    fmt: Optional[OutputFormat] = typer.Option(None, "--format"),
    prompt: Path = typer.Option(
        Path("prompts/validate-output.prompt.yaml"),
        help="Prompt file",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model name override"
    ),
    base_model_url: Optional[str] = typer.Option(
        None, "--base-model-url", help="Model base URL override"
    ),
) -> None:
    """Validate converted output against the original file."""
    validate_doc(raw, rendered, fmt, prompt, model, base_model_url)


@app.command()
def analyze(
    prompt: Path = typer.Argument(..., help="Prompt file"),
    markdown_doc: Path = typer.Argument(..., help="Markdown document"),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Optional output file; defaults to <doc>.<prompt>.json",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model name override"
    ),
    base_model_url: Optional[str] = typer.Option(
        None, "--base-model-url", help="Model base URL override"
    ),
) -> None:
    """Run an analysis prompt against a Markdown document."""
    analyze_doc(prompt, markdown_doc, output, model, base_model_url)


@app.command()
def embed(
    source: Path = typer.Argument(..., help="Directory containing Markdown files"),
) -> None:
    """Generate embeddings for Markdown files."""
    build_vector_store(source)


@app.command("pipeline")
def pipeline(
    source: Path = typer.Argument(..., help="Directory with raw documents"),
    prompt: Path = typer.Option(
        Path("prompts/doc-analysis.prompt.yaml"),
        help="Analysis prompt file",
    ),
    format: List[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s) for conversion",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model name override"
    ),
    base_model_url: Optional[str] = typer.Option(
        None, "--base-model-url", help="Model base URL override"
    ),
) -> None:
    """Run the full pipeline: convert, validate, analyze, and embed."""
    env_fmts = _parse_env_formats()
    fmts = format or env_fmts or [OutputFormat.MARKDOWN]
    convert_path(source, fmts)
    validation_prompt = Path("prompts/validate-output.prompt.yaml")
    for raw_file in source.rglob("*"):
        if not raw_file.is_file():
            continue
        md_file = raw_file.with_name(raw_file.name + _suffix(OutputFormat.MARKDOWN))
        if md_file.exists():
            validate_doc(
                raw_file,
                md_file,
                OutputFormat.MARKDOWN,
                validation_prompt,
                model,
                base_model_url,
            )
            analyze_doc(prompt, md_file, model=model, base_url=base_model_url)
    build_vector_store(source)


__all__ = ["app"]


if __name__ == "__main__":
    app()
