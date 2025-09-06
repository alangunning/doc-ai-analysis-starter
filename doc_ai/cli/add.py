from __future__ import annotations

from pathlib import Path

import typer

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
    """Write *urls* to *path* atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(urls) + ("\n" if urls else ""))
    tmp.replace(path)


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


@app.command("urls")
def add_urls(
    ctx: typer.Context,
    path: Path = typer.Argument(..., help="File containing URLs"),
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
    """Download URLs from *path* and convert them."""

    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    fmts = format or _parse_config_formats(cfg) or [OutputFormat.MARKDOWN]
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")
    links = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if not links:
        typer.echo("No URLs found in file.")
        return
    download_and_convert(links, doc_type, fmts, force)


@app.command("manage-urls")
def manage_urls(doc_type: str = typer.Argument(..., help="Document type")) -> None:
    """Interactively manage stored URLs for *doc_type*."""

    path, urls = show_urls(doc_type)
    while True:
        choice = typer.prompt(
            "Enter URL to add, number to remove, or blank to finish",
            default="",
        ).strip()
        if not choice:
            break
        if choice.isdigit() and 1 <= int(choice) <= len(urls):
            urls.pop(int(choice) - 1)
        else:
            urls.append(choice)
    save_urls(path, urls)

