from __future__ import annotations

from pathlib import Path

import questionary
import typer

from doc_ai.converter import OutputFormat

from .convert import download_and_convert
from .interactive import discover_doc_types_topics
from .manage_urls import _valid_url
from .utils import (
    parse_config_formats as _parse_config_formats,
)
from .utils import (
    prompt_if_missing,
    resolve_bool,
)

app = typer.Typer(help="Add documents to the data directory.")


@app.command("url")
def add_url(
    ctx: typer.Context,
    link: str | None = typer.Argument(None, help="URL to download"),
    doc_type: str | None = typer.Option(None, "--doc-type", help="Document type"),
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
    ),
) -> None:
    """Download *link* and convert it under ``data/<doc-type>/``."""

    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    link = prompt_if_missing(ctx, link, "URL to download")
    if link is None:
        raise typer.BadParameter("URL to download required")
    doc_type = doc_type or cfg.get("default_doc_type")
    if doc_type is None:
        doc_types, _ = discover_doc_types_topics()
        if doc_types:
            try:
                doc_type = questionary.select(
                    "Select document type", choices=doc_types
                ).ask()
            except Exception:
                doc_type = None
        doc_type = prompt_if_missing(ctx, doc_type, "Document type")
    if doc_type is None:
        raise typer.BadParameter("Document type required")
    fmts = format or _parse_config_formats(cfg) or [OutputFormat.MARKDOWN]
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")
    if not _valid_url(link):
        raise typer.BadParameter("Invalid URL")
    download_and_convert([link], doc_type, fmts, force)


@app.command("urls")
def add_urls(
    ctx: typer.Context,
    path: Path | None = typer.Argument(None, help="File containing URLs"),
    doc_type: str | None = typer.Option(None, "--doc-type", help="Document type"),
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
    ),
) -> None:
    """Download URLs from *path* and convert them."""

    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    path_val = prompt_if_missing(
        ctx, str(path) if path is not None else None, "File containing URLs"
    )
    if path_val is None:
        raise typer.BadParameter("File containing URLs required")
    path = Path(path_val)
    doc_type = doc_type or cfg.get("default_doc_type")
    if doc_type is None:
        doc_types, _ = discover_doc_types_topics()
        if doc_types:
            try:
                doc_type = questionary.select(
                    "Select document type", choices=doc_types
                ).ask()
            except Exception:
                doc_type = None
        doc_type = prompt_if_missing(ctx, doc_type, "Document type")
    if doc_type is None:
        raise typer.BadParameter("Document type required")
    fmts = format or _parse_config_formats(cfg) or [OutputFormat.MARKDOWN]
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")
    links: list[str] = []
    seen: set[str] = set()
    for line in path.read_text().splitlines():
        url = line.strip()
        if not url:
            continue
        if not _valid_url(url):
            typer.echo(f"Skipping invalid URL: {url}")
            continue
        if url in seen:
            typer.echo(f"Skipping duplicate URL: {url}")
            continue
        seen.add(url)
        links.append(url)
    if not links:
        typer.echo("No valid URLs found in file.")
        return
    download_and_convert(links, doc_type, fmts, force)
