from __future__ import annotations

from pathlib import Path

import typer

from doc_ai.converter import OutputFormat
from .convert import download_and_convert
from .utils import parse_config_formats as _parse_config_formats, resolve_bool

app = typer.Typer(help="Add documents to the data directory.")


@app.command("url")
def add_url(
    ctx: typer.Context,
    link: str = typer.Argument(..., help="URL to download"),
    doc_type: str = typer.Option(..., "--doc-type", help="Document type"),
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
    """Download *link* and convert it under ``data/<doc-type>/``."""

    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    fmts = format or _parse_config_formats(cfg) or [OutputFormat.MARKDOWN]
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")
    download_and_convert([link], doc_type, fmts, force)

