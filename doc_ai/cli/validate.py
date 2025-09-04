from __future__ import annotations

from pathlib import Path
from typing import Optional
import logging

import typer
from rich.console import Console

from doc_ai.converter import OutputFormat
from .utils import infer_format as _infer_format, suffix as _suffix, validate_doc
from . import ModelName, _validate_prompt

app = typer.Typer(invoke_without_command=True, help="Validate converted output against the original file.")


@app.callback()
def validate(
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
        None, "--base-model-url",
        envvar="VALIDATE_BASE_MODEL_URL",
        help="Model base URL override"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Write request/response details to this file"
    ),
) -> None:
    """Validate converted output against the original file."""
    logger: logging.Logger | None = None
    log_path = log_file
    console_local = Console()
    if verbose or log_path is not None:
        logger = logging.getLogger("doc_ai.validate")
        logger.setLevel(logging.DEBUG)
        if verbose:
            from rich.logging import RichHandler

            sh = RichHandler(console=console_local, show_time=False)
            sh.setLevel(logging.DEBUG)
            logger.addHandler(sh)
        if log_path is None:
            log_path = raw.with_suffix(".validate.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)

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
        logger=logger,
        console=console_local,
    )
