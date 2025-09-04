from __future__ import annotations

from pathlib import Path
import logging

import typer

from doc_ai.converter import OutputFormat
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
) -> None:
    """Convert files using Docling.

    Examples:
        doc-ai convert report.pdf
    """
    if ctx.obj is None:
        ctx.obj = {}
    from . import convert_path as _convert_path

    cfg = ctx.obj.get("config", {})
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")
    fmts = format or _parse_config_formats(cfg) or [OutputFormat.MARKDOWN]
    try:
        if source.startswith(("http://", "https://")):
            results = _convert_path(source, fmts, force=force)
        else:
            results = _convert_path(Path(source), fmts, force=force)
    except Exception as exc:  # pragma: no cover - error handling
        logger.error(str(exc))
        raise typer.Exit(1)

    if not results:
        logger.warning("No new files to process.")
