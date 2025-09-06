from __future__ import annotations

from pathlib import Path
import logging
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import typer

from doc_ai.converter import OutputFormat

from doc_ai.utils import http_get, sanitize_filename
from rich.progress import Progress

from .utils import parse_config_formats as _parse_config_formats, resolve_bool

logger = logging.getLogger(__name__)

app = typer.Typer(invoke_without_command=True, help="Convert files using Docling.")


def download_and_convert(
    urls: list[str],
    doc_type: str,
    formats: list[OutputFormat],
    force: bool,
) -> dict[Path, tuple[dict[OutputFormat, Path], object]]:
    """Download *urls* into ``data/<doc_type>/`` and convert them."""

    from . import convert_path as _convert_path

    dest = Path("data") / doc_type
    dest.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    lock = Lock()

    def _download(link: str) -> None:
        resp = http_get(link, stream=True)
        try:
            resp.raise_for_status()
            name = Path(urlparse(link).path).name or "downloaded"
            with lock:
                sanitized = sanitize_filename(name, existing=seen)
                seen.add(sanitized)
            path = dest / sanitized
            with open(path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    fh.write(chunk)
        finally:
            resp.close()

    with Progress(transient=True) as progress:
        task = progress.add_task(f"Downloading {doc_type}", total=len(urls))
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(_download, link) for link in urls]
            for fut in as_completed(futures):
                fut.result()
                progress.advance(task)

    return _convert_path(dest, formats, force=force)


@app.callback()
def convert(
    ctx: typer.Context,
    source: str | None = typer.Argument(
        None, help="Path or URL to raw document or folder",
    ),
    url: list[str] = typer.Option(
        None,
        "--url",
        help="URL to download and convert. Can be passed multiple times.",
    ),
    urls: Path | None = typer.Option(
        None,
        "--urls",
        help="File containing URLs to download (one per line).",
    ),
    doc_type: str | None = typer.Option(
        None, "--doc-type", help="Document type for downloaded URLs",
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
        doc-ai convert report.pdf --verbose
        doc-ai --log-level INFO convert report.pdf
        doc-ai convert --doc-type reports --url https://example.com/a.pdf --url https://example.com/b.pdf
    """
    if ctx.obj is None:
        ctx.obj = {}
    from . import convert_path as _convert_path

    cfg = ctx.obj.get("config", {})
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")
    fmts = format or _parse_config_formats(cfg) or [OutputFormat.MARKDOWN]
    url_list: list[str] = []
    if urls is not None:
        url_list.extend(
            line.strip() for line in urls.read_text().splitlines() if line.strip()
        )
    if url:
        url_list.extend(url)
    results: dict[Path, tuple[dict[OutputFormat, Path], object]] = {}
    if url_list:
        if doc_type is None:
            raise typer.BadParameter("--doc-type is required when providing URLs")
        results.update(download_and_convert(url_list, doc_type, fmts, force))
    if source is not None:
        try:
            if source.startswith(("http://", "https://")):
                results.update(_convert_path(source, fmts, force=force))
            else:
                results.update(_convert_path(Path(source), fmts, force=force))
        except Exception as exc:  # pragma: no cover - error handling
            logger.error(str(exc))
            raise typer.Exit(1)

    if not results:
        logger.warning("No new files to process.")

