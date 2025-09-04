"""Shared utilities for doc_ai CLI."""
from __future__ import annotations

from pathlib import Path
from typing import Callable
import logging
import os
import re
import functools
from datetime import datetime, timezone

import typer
from rich.console import Console
from dotenv import dotenv_values

from doc_ai.converter import OutputFormat, suffix_for_format
from doc_ai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)

# Mapping of file extensions to output formats used across commands
EXTENSION_MAP = {
    ".md": OutputFormat.MARKDOWN,
    ".html": OutputFormat.HTML,
    ".json": OutputFormat.JSON,
    ".txt": OutputFormat.TEXT,
    ".doctags": OutputFormat.DOCTAGS,
    ".dogtags": OutputFormat.DOCTAGS,
}


def suffix(fmt: OutputFormat) -> str:
    """Return the standard suffix for a converted file."""
    return f".converted{suffix_for_format(fmt)}"


def infer_format(path: Path) -> OutputFormat:
    """Infer an output format from a file extension."""
    try:
        return EXTENSION_MAP[path.suffix.lower()]
    except KeyError as exc:
        valid = ", ".join(EXTENSION_MAP.keys())
        raise typer.BadParameter(
            f"Unknown file extension '{path.suffix}'. Expected one of: {valid}"
        ) from exc


def parse_env_formats() -> list[OutputFormat] | None:
    """Return formats from OUTPUT_FORMATS env var if set."""
    env_val = os.getenv("OUTPUT_FORMATS")
    if not env_val:
        return None
    formats: list[OutputFormat] = []
    for val in env_val.split(","):
        try:
            formats.append(OutputFormat(val.strip()))
        except ValueError as exc:
            valid = ", ".join(f.value for f in OutputFormat)
            raise typer.BadParameter(
                f"Invalid output format '{val}'. Choose from: {valid}"
            ) from exc
    return formats


@functools.lru_cache()
def load_env_defaults() -> dict[str, str | None]:
    """Load default settings from the repository's .env.example file."""
    example_path = Path(__file__).resolve().parents[2] / ".env.example"
    if example_path.exists():
        return dotenv_values(example_path)  # type: ignore[return-value]
    return {}


def validate_doc(
    raw: Path,
    rendered: Path,
    fmt: OutputFormat | None = None,
    prompt: Path | None = None,
    model: str | None = None,
    base_url: str | None = None,
    show_progress: bool = False,
    logger: logging.Logger | None = None,
    console: Console | None = None,
    validate_file_func: Callable | None = None,
) -> None:
    """Validate a converted document against its raw source."""
    if validate_file_func is None:
        from doc_ai.cli import validate_file as validate_file_func  # type: ignore

    meta = load_metadata(raw)
    file_hash = compute_hash(raw)
    if meta.blake2b == file_hash and is_step_done(meta, "validation"):
        return
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}
    if fmt is None:
        fmt = EXTENSION_MAP.get(rendered.suffix)
        if fmt is None:
            valid = ", ".join(EXTENSION_MAP.keys())
            raise typer.BadParameter(
                f"Unknown file extension '{rendered.suffix}'. Expected one of: {valid}"
            )
    prompt_path = prompt
    if prompt_path is None:
        doc_prompt = raw.with_name(f"{raw.stem}.validate.prompt.yaml")
        dir_prompt = raw.with_name("validate.prompt.yaml")
        if doc_prompt.exists():
            prompt_path = doc_prompt
        elif dir_prompt.exists():
            prompt_path = dir_prompt
        else:
            prompt_path = Path(
                ".github/prompts/validate-output.validate.prompt.yaml"
            )
    verdict = validate_file_func(
        raw,
        rendered,
        fmt,
        prompt_path,
        model=model,
        base_url=base_url,
        show_progress=show_progress,
        logger=logger,
        console=console,
    )
    match = verdict.get("match", False)
    now = datetime.now(timezone.utc).isoformat()
    meta.date_modified = now
    mark_step(
        meta,
        "validation",
        done=match,
        outputs=[rendered.name],
        inputs={
            "prompt": prompt_path.name,
            "rendered": rendered.name,
            "rendered_blake2b": compute_hash(rendered),
            "format": fmt.value,
            "model": model,
            "base_url": base_url,
            "document": str(raw),
            "validated_at": now,
            "verdict": verdict,
        },
    )
    save_metadata(raw, meta)
    if not match:
        raise RuntimeError(f"Mismatch detected: {verdict}")


def analyze_doc(
    markdown_doc: Path,
    prompt: Path | None = None,
    output: Path | None = None,
    model: str | None = None,
    base_url: str | None = None,
    run_prompt_func: Callable | None = None,
) -> None:
    """Run an analysis prompt on a markdown document and store results."""
    if run_prompt_func is None:
        from doc_ai.cli import run_prompt as run_prompt_func  # type: ignore

    step_name = "analysis"
    raw_doc = markdown_doc
    if ".converted" in markdown_doc.suffixes:
        raw_doc = raw_doc.with_suffix("").with_suffix("")
    meta = load_metadata(raw_doc)
    md_hash = compute_hash(markdown_doc)
    prev_hash = None
    if meta.extra:
        prev_hash = (
            meta.extra.get("inputs", {})
            .get(step_name, {})
            .get("markdown_blake2b")
        )
    if is_step_done(meta, step_name) and prev_hash == md_hash:
        return

    prompt_path = prompt
    if prompt_path is None:
        type_prompt = markdown_doc.parent / (
            f"{markdown_doc.parent.name}.analysis.prompt.yaml"
        )
        dir_prompt = markdown_doc.parent / "analysis.prompt.yaml"
        if type_prompt.exists():
            prompt_path = type_prompt
        elif dir_prompt.exists():
            prompt_path = dir_prompt
        else:
            prompt_path = Path(
                ".github/prompts/doc-analysis.analysis.prompt.yaml"
            )

    result = run_prompt_func(
        prompt_path,
        markdown_doc.read_text(),
        model=model,
        base_url=base_url,
    )
    result = result.strip()
    fence = re.match(r"```(?:json)?\n([\s\S]*?)\n```", result)
    if fence:
        result = fence.group(1).strip()
    if output:
        out_path = output
    else:
        base = markdown_doc
        if base.suffix == ".md":
            base = base.with_suffix("")
        if base.suffix == ".converted":
            base = base.with_suffix("")
        out_path = base.with_name(f"{base.name}.analysis.json")
    out_path.write_text(result + "\n", encoding="utf-8")
    from doc_ai.cli import console as _console
    _console.print(
        f"[green]Analyzed {markdown_doc} -> {out_path} (SUCCESS)[/]"
    )
    mark_step(
        meta,
        step_name,
        outputs=[out_path.name],
        inputs={
            "prompt": prompt_path.name,
            "markdown": markdown_doc.name,
            "markdown_blake2b": md_hash,
        },
    )
    save_metadata(raw_doc, meta)
