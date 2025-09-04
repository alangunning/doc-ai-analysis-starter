from __future__ import annotations

from pathlib import Path
import logging

import typer

from doc_ai.converter import OutputFormat
from doc_ai.logging import configure_logging
from .utils import parse_config_formats as _parse_config_formats, resolve_bool

logger = logging.getLogger(__name__)

app = typer.Typer(invoke_without_command=True, help="Convert files using Docling.")


@app.callback()
def convert(
    ctx: typer.Context,
    source: str = typer.Argument(
        ..., help="Path or URL to raw document or folder"
    ),
    format: list[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s). Can be passed multiple times.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Re-run conversion even if metadata is present",
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
    """Convert files using Docling.

    Examples:
        doc-ai convert report.pdf --verbose
        doc-ai --log-level INFO convert report.pdf
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
    from . import convert_path as _convert_path

    cfg = ctx.obj.get("config", {})
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")
    fmts = format or _parse_config_formats(cfg) or [OutputFormat.MARKDOWN]
    if source.startswith(("http://", "https://")):
        results = _convert_path(source, fmts, force=force)
    else:
        results = _convert_path(Path(source), fmts, force=force)

    if not results:
        logger.warning("No new files to process.")
