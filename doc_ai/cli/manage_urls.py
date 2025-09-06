from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import questionary
import typer

from .interactive import refresh_completer, discover_doc_types_topics
from .utils import prompt_if_missing


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
    unique = list(dict.fromkeys(urls))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(unique) + ("\n" if unique else ""))
    tmp.replace(path)


def _valid_url(url: str) -> bool:
    """Return ``True`` if *url* looks like an HTTP/HTTPS URL."""
    parsed = urlparse(url)
    return bool(parsed.scheme in {"http", "https"} and parsed.netloc)


def manage_urls(
    ctx: typer.Context, doc_type: str | None = typer.Argument(None, help="Document type")
) -> None:
    """Interactively manage stored URLs for *doc_type*."""
    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    doc_type = doc_type or cfg.get("default_doc_type")
    if doc_type is None:
        doc_types, _ = discover_doc_types_topics()
        if doc_types:
            try:
                doc_type = questionary.select("Select document type", choices=doc_types).ask()
            except Exception:
                doc_type = None
        doc_type = prompt_if_missing(ctx, doc_type, "Document type")
    if doc_type is None:
        raise typer.BadParameter("Document type required")

    path, urls = show_urls(doc_type)

    while True:
        try:
            action = questionary.select(
                "Choose action",
                choices=["list", "add", "remove", "done"],
            ).ask()
        except Exception:
            action = "done"
        if action in (None, "done"):
            break
        if action == "list":
            path, urls = show_urls(doc_type)
            continue
        if action == "add":
            try:
                url = questionary.text("Enter URL").ask()
            except Exception:
                url = None
            if not url:
                continue
            url = url.strip()
            if not _valid_url(url):
                typer.echo(f"Skipping invalid URL: {url}")
                continue
            urls.append(url)
            save_urls(path, urls)
            refresh_completer()
            continue
        if action == "remove":
            if not urls:
                typer.echo("No URLs to remove.")
                continue
            try:
                to_remove = questionary.select(
                    "Select URL to remove", choices=urls
                ).ask()
            except Exception:
                to_remove = None
            if not to_remove:
                continue
            urls = [u for u in urls if u != to_remove]
            save_urls(path, urls)
            refresh_completer()
            continue
