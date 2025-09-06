from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import questionary
import typer

from .interactive import refresh_completer

from doc_ai.converter import OutputFormat
from .convert import download_and_convert
from .utils import parse_config_formats as _parse_config_formats, resolve_bool

app = typer.Typer(help="Add documents to the data directory.")


def _url_file(doc_type: str) -> Path:
    """Return path to the persistent URL list for ``doc_type``."""

    return Path("data") / doc_type / "urls.txt"


def show_urls(doc_type: str) -> tuple[Path, list[str]]:
    """Display and return stored URLs for ``doc_type``."""

    path = _url_file(doc_type)
    urls: list[str] = []
    if path.exists():
        urls = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if urls:
        typer.echo("Current URLs:")
        for i, url in enumerate(urls, 1):
            typer.echo(f"{i}. {url}")
    else:
        typer.echo("No URLs configured.")
    return path, urls


def save_urls(path: Path, urls: list[str]) -> None:
    """Write *urls* to *path* atomically after removing duplicates."""

    # Preserve order while removing duplicates
    unique = list(dict.fromkeys(urls))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(unique) + ("\n" if unique else ""))
    tmp.replace(path)


def _valid_url(url: str) -> bool:
    """Return ``True`` if *url* looks like an HTTP/HTTPS URL."""

    parsed = urlparse(url)
    return bool(parsed.scheme in {"http", "https"} and parsed.netloc)


@app.command("url")
def add_url(
    ctx: typer.Context,
    link: str = typer.Argument(..., help="URL to download"),
    doc_type: str | None = typer.Option(
        None, "--doc-type", help="Document type"
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
    """Download *link* and convert it under ``data/<doc-type>/``."""

    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    doc_type = doc_type or cfg.get("default_doc_type")
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
    path: Path = typer.Argument(..., help="File containing URLs"),
    doc_type: str | None = typer.Option(
        None, "--doc-type", help="Document type"
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
    """Download URLs from *path* and convert them."""

    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    doc_type = doc_type or cfg.get("default_doc_type")
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


@app.command("manage-urls")
def manage_urls(
    ctx: typer.Context,
    doc_type: str | None = typer.Argument(None, help="Document type"),
) -> None:
    """Interactively manage stored URLs for *doc_type*."""
    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    doc_type = doc_type or cfg.get("default_doc_type")
    if doc_type is None:
        raise typer.BadParameter("Document type required")
    path, urls = show_urls(doc_type)
    edited = questionary.text(
        "Edit URLs (one per line)",
        default="\n".join(urls),
        multiline=True,
    ).ask()
    if edited is None:
        return

    new_urls: list[str] = []
    for line in edited.splitlines():
        url = line.strip()
        if not url:
            continue
        if not _valid_url(url):
            typer.echo(f"Skipping invalid URL: {url}")
            continue
        new_urls.append(url)
    save_urls(path, new_urls)
    refresh_completer()
