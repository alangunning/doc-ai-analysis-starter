from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import logging

import typer

from doc_ai.converter import OutputFormat, convert_path
from doc_ai.logging import configure_logging
from doc_ai.utils import http_get
from .utils import parse_config_formats as _parse_config_formats, resolve_bool

logger = logging.getLogger(__name__)

app = typer.Typer(invoke_without_command=True, help="Download documents from URLs and convert them.")


def _download(url: str, doc_type: str, data_dir: Path = Path("data")) -> Path:
    resp = http_get(url, stream=True)
    resp.raise_for_status()
    name = Path(urlparse(url).path).name or "downloaded"
    dest_dir = data_dir / doc_type
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / name
    with open(dest, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                fh.write(chunk)
    resp.close()
    return dest


def _record(url: str, doc_type: str, url_file: Path = Path("urls.txt")) -> None:
    with url_file.open("a", encoding="utf-8") as fh:
        fh.write(f"{doc_type}\t{url}\n")


def process_urls(
    urls: list[str],
    doc_type: str,
    fmts: list[OutputFormat] | None = None,
    *,
    force: bool = False,
    data_dir: Path = Path("data"),
) -> None:
    fmts = fmts or [OutputFormat.MARKDOWN]
    for url in urls:
        dest = _download(url, doc_type, data_dir)
        convert_path(dest, fmts, force=force)
        _record(url, doc_type)


@app.callback()
def import_urls(
    ctx: typer.Context,
    url: list[str] = typer.Option(
        None,
        "--url",
        help="Remote document URL. Can be repeated.",
    ),
    urls: Path | None = typer.Option(
        None,
        "--urls",
        help="File containing URLs, one per line.",
    ),
    doc_type: str = typer.Option(
        ...,
        "--doc-type",
        help="Document type directory under data/.",
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
    cfg = ctx.obj.get("config", {})
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")
    fmts = format or _parse_config_formats(cfg) or [OutputFormat.MARKDOWN]
    url_list = list(url)
    if urls is not None:
        url_list.extend([line.strip() for line in urls.read_text().splitlines() if line.strip()])
    if not url_list:
        logger.error("No URLs provided.")
        raise typer.Exit(1)
    try:
        process_urls(url_list, doc_type, fmts, force=force)
    except Exception as exc:  # pragma: no cover - error handling
        logger.error(str(exc))
        raise typer.Exit(1)
