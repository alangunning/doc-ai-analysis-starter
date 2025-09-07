from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

import questionary
import typer

from .interactive import refresh_completer
from .utils import select_doc_type

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="Manage stored URLs; paste or import multiple entries.",
    invoke_without_command=True,
)


def _url_file(doc_type: str) -> Path:
    """Return path to the persistent URL list for ``doc_type``."""
    return Path("data") / doc_type / "urls.txt"


def _load_urls(doc_type: str) -> tuple[Path, list[str]]:
    """Return the path and stored URLs for ``doc_type``."""
    path = _url_file(doc_type)
    urls: list[str] = []
    if path.exists():
        urls = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    return path, urls


def show_urls(doc_type: str) -> tuple[Path, list[str]]:
    """Display and return stored URLs for ``doc_type``."""
    path, urls = _load_urls(doc_type)
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


@app.command("list")
def list_urls(
    ctx: typer.Context,
    doc_type: str | None = typer.Option(None, "--doc-type", help="Document type"),
) -> None:
    """List stored URLs for *doc_type*."""
    doc_type = select_doc_type(ctx, doc_type)
    show_urls(doc_type)


@app.command("add")
def add_urls(
    ctx: typer.Context,
    url: list[str] | None = typer.Option(
        None, "--url", help="URL to add", metavar="URL"
    ),
    doc_type: str | None = typer.Option(None, "--doc-type", help="Document type"),
) -> None:
    """Add one or more URLs for *doc_type*."""
    doc_type = select_doc_type(ctx, doc_type)
    path, urls = _load_urls(doc_type)
    if not url:
        try:
            raw = questionary.text("Enter URL(s)").ask()
        except Exception:
            logger.exception("Failed to read URL input")
            raw = None
        if not raw:
            raise typer.BadParameter("URL required")
        url = raw.split()
    new_urls: list[str] = []
    for entry in url:
        entry = entry.strip()
        if not _valid_url(entry):
            typer.echo(f"Skipping invalid URL: {entry}")
            continue
        if entry in urls:
            typer.echo(f"Skipping duplicate URL: {entry}")
            continue
        urls.append(entry)
        new_urls.append(entry)
    if new_urls:
        save_urls(path, urls)
        refresh_completer()


@app.command("import")
def import_urls(
    ctx: typer.Context,
    file: Path | None = typer.Option(
        None, "--file", "-f", help="Path to file with URLs"
    ),
    doc_type: str | None = typer.Option(None, "--doc-type", help="Document type"),
) -> None:
    """Import URLs from *file* for *doc_type*."""
    doc_type = select_doc_type(ctx, doc_type)
    if file is None:
        try:
            path_str = questionary.text("Path to file with URLs").ask()
        except Exception:
            logger.exception("Failed to read path input")
            path_str = None
        if not path_str:
            raise typer.BadParameter("Path to file with URLs required")
        file = Path(path_str)
    file_path = file.expanduser()
    if not file_path.exists():
        raise typer.BadParameter(f"File not found: {file_path}")
    raw = file_path.read_text()
    path, urls = _load_urls(doc_type)
    new_urls: list[str] = []
    for entry in raw.split():
        entry = entry.strip()
        if not _valid_url(entry):
            typer.echo(f"Skipping invalid URL: {entry}")
            continue
        if entry in urls:
            typer.echo(f"Skipping duplicate URL: {entry}")
            continue
        urls.append(entry)
        new_urls.append(entry)
    if new_urls:
        save_urls(path, urls)
        refresh_completer()


@app.command("remove")
def remove_url(
    ctx: typer.Context,
    url: str | None = typer.Option(None, "--url", help="URL to remove"),
    doc_type: str | None = typer.Option(None, "--doc-type", help="Document type"),
) -> None:
    """Remove a stored URL for *doc_type*."""
    doc_type = select_doc_type(ctx, doc_type)
    path, urls = _load_urls(doc_type)
    if not urls:
        typer.echo("No URLs to remove.")
        return
    if url is None:
        try:
            url = questionary.select("Select URL to remove", choices=urls).ask()
        except Exception:
            logger.exception("Failed to select URL to remove")
            url = None
        if not url:
            raise typer.BadParameter("URL to remove required")
    if url not in urls:
        typer.echo(f"URL not found: {url}")
        return
    urls = [u for u in urls if u != url]
    save_urls(path, urls)
    refresh_completer()


@app.callback()
def manage_urls(ctx: typer.Context) -> None:
    """Interactively manage stored URLs for *doc_type*.

    Use "add" to enter one or more URLs separated by whitespace or newlines, or
    "import" to load URLs from a text file.
    """
    if ctx.invoked_subcommand:
        return

    doc_type = select_doc_type(ctx, None)

    path, urls = show_urls(doc_type)

    while True:
        try:
            action = questionary.select(
                "Choose action",
                choices=["list", "add", "import", "remove", "done"],
            ).ask()
        except Exception:
            logger.exception("Failed to prompt for action")
            action = "done"
        if action in (None, "done"):
            break
        if action == "list":
            path, urls = show_urls(doc_type)
            continue
        if action == "add":
            try:
                raw = questionary.text("Enter URL(s)").ask()
            except Exception:
                logger.exception("Failed to read URL input")
                raw = None
            if not raw:
                continue
            new_urls: list[str] = []
            for url in raw.split():
                url = url.strip()
                if not _valid_url(url):
                    typer.echo(f"Skipping invalid URL: {url}")
                    continue
                if url in urls:
                    typer.echo(f"Skipping duplicate URL: {url}")
                    continue
                urls.append(url)
                new_urls.append(url)
            if new_urls:
                save_urls(path, urls)
                refresh_completer()
            continue
        if action == "import":
            try:
                import_path = questionary.text("Path to file with URLs").ask()
            except Exception:
                logger.exception("Failed to read path input")
                import_path = None
            if not import_path:
                continue
            file_path = Path(import_path).expanduser()
            if not file_path.exists():
                typer.echo(f"File not found: {file_path}")
                continue
            raw = file_path.read_text()
            new_urls: list[str] = []
            for url in raw.split():
                url = url.strip()
                if not _valid_url(url):
                    typer.echo(f"Skipping invalid URL: {url}")
                    continue
                if url in urls:
                    typer.echo(f"Skipping duplicate URL: {url}")
                    continue
                urls.append(url)
                new_urls.append(url)
            if new_urls:
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
                logger.exception("Failed to select URL to remove")
                to_remove = None
            if not to_remove:
                continue
            urls = [u for u in urls if u != to_remove]
            save_urls(path, urls)
            refresh_completer()
            continue
