from __future__ import annotations

from pathlib import Path
from typing import Optional
import logging

import typer
from rich.console import Console

from doc_ai.converter import OutputFormat
from doc_ai.logging import configure_logging
from .utils import infer_format as _infer_format, suffix as _suffix, validate_doc
from . import ModelName, _validate_prompt

app = typer.Typer(
    invoke_without_command=True,
    help="Validate converted output against the original file.",
)


@app.callback()
def validate(
    ctx: typer.Context,
    raw: Path = typer.Argument(..., help="Path to raw document"),
    rendered: Path | None = typer.Argument(
        None, help="Path to converted file"
    ),
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f"),
    prompt: Optional[Path] = typer.Option(
        None,
        "--prompt",
        help="Prompt file (overrides auto-detected *.validate.prompt.yaml)",
        callback=_validate_prompt,
    ),
    model: Optional[ModelName] = typer.Option(
        None,
        "--model",
        envvar="VALIDATE_MODEL",
        help="Model name override",
    ),
    base_model_url: Optional[str] = typer.Option(
        None,
        "--base-model-url",
        envvar="VALIDATE_BASE_MODEL_URL",
        help="Model base URL override",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Re-run validation even if metadata is present",
        is_flag=True,
    ),
    verbose: bool | None = typer.Option(
        None, "--verbose", "-v", help="Shortcut for --log-level DEBUG"
    ),
    log_level: str | None = typer.Option(
        None, "--log-level", help="Logging level (e.g. INFO, DEBUG)"
    ),
    log_file: Path | None = typer.Option(
        None, "--log-file", help="Write logs to the given file"
    ),
) -> None:
    """Validate converted output against the original file.

    Examples:
        doc-ai validate report.pdf --verbose
        doc-ai --log-file validate.log validate report.pdf converted.md
    """
    if ctx.obj is None:
        ctx.obj = {}
    if any(opt is not None for opt in (verbose, log_level, log_file)):
        level_name = "DEBUG" if verbose else log_level or logging.getLevelName(
            logging.getLogger().level
        )
        configure_logging(level_name, log_file)
        ctx.obj["verbose"] = logging.getLogger().level <= logging.DEBUG
        ctx.obj["log_level"] = level_name
        ctx.obj["log_file"] = log_file
    console_local = Console()
    if rendered is None:
        used_fmt = fmt or OutputFormat.MARKDOWN
        rendered = raw.with_name(raw.name + _suffix(used_fmt))
    else:
        used_fmt = fmt or _infer_format(rendered)

    validate_doc(
        raw,
        rendered,
        used_fmt,
        prompt,
        model,
        base_model_url,
        show_progress=True,
        console=console_local,
        force=force,
    )

