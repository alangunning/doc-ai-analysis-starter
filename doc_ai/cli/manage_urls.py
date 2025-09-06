from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import questionary
import typer

from .interactive import refresh_completer, discover_doc_types_topics
from .utils import prompt_if_missing


app = typer.Typer(
    help="Manage stored URLs; paste or import multiple entries.",
    invoke_without_command=True,
)


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


@app.command("wizard", help="Bulk add URLs using a form.")
def url_wizard(ctx: typer.Context) -> None:
    """Prompt for a document type and URLs to append via a textarea."""

    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    doc_types, _ = discover_doc_types_topics()
    doc_q = (
        questionary.select("Document type", choices=doc_types)
        if doc_types
        else questionary.text("Document type")
    )
    textarea = getattr(questionary, "textarea", None)
    try:
        answers = questionary.form(
            doc_type=doc_q,
            urls=textarea("Enter URLs, one per line") if callable(textarea) else questionary.text("Enter URLs"),
        ).ask()
    except Exception:
        answers = None
    if not answers:
        return

    doc_type = answers.get("doc_type") or cfg.get("default_doc_type")
    if not doc_type:
        raise typer.BadParameter("Document type required")
    doc_type = str(doc_type)
    path, existing = show_urls(doc_type)
    raw = answers.get("urls") or ""
    for url in raw.splitlines():
        url = url.strip()
        if not url or not _valid_url(url) or url in existing:
            continue
        existing.append(url)
    save_urls(path, existing)
    refresh_completer()


def edit_url_list(ctx: typer.Context, doc_type: str | None = None) -> None:
    """Edit the persistent URL list for *doc_type* via an inline editor."""

    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
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

    path, urls = show_urls(doc_type)
    default = "\n".join(urls)
    textarea = getattr(questionary, "textarea", None)
    edited: str | None = None
    if callable(textarea):
        try:
            edited = textarea("Edit URLs", default=default).ask()
        except Exception:
            edited = None
    if edited is None:
        edited = typer.edit(default)
    if edited is None:
        return

    new_urls: list[str] = []
    for line in edited.splitlines():
        u = line.strip()
        if not u or not _valid_url(u):
            continue
        if u not in new_urls:
            new_urls.append(u)
    save_urls(path, new_urls)
    refresh_completer()


@app.callback()
def manage_urls(
    ctx: typer.Context, doc_type: str | None = typer.Argument(None, help="Document type")
) -> None:
    """Interactively manage stored URLs for *doc_type*.

    Use "add" to enter one or more URLs separated by whitespace or newlines, or
    "import" to load URLs from a text file.
    """
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
                choices=["list", "add", "import", "remove", "done"],
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
                raw = questionary.text("Enter URL(s)").ask()
            except Exception:
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
                to_remove = None
            if not to_remove:
                continue
            urls = [u for u in urls if u != to_remove]
            save_urls(path, urls)
            refresh_completer()
            continue
