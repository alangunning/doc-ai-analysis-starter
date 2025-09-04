from __future__ import annotations

from pathlib import Path
import logging

import typer

from doc_ai.logging import configure_logging
from . import build_vector_store

app = typer.Typer(invoke_without_command=True, help="Generate embeddings for Markdown files.")


@app.callback()
def embed(
    ctx: typer.Context,
    source: Path = typer.Argument(..., help="Directory containing Markdown files"),
    fail_fast: bool = typer.Option(
        False, "--fail-fast", help="Abort immediately on the first HTTP error"
    ),
    workers: int = typer.Option(
        1, "--workers", "-w", help="Number of worker threads"
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
    """Generate embeddings for Markdown files.

    Examples:
        doc-ai embed docs/ --verbose
        doc-ai --log-file embed.log embed docs/
    """
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
    build_vector_store(source, fail_fast=fail_fast, workers=workers)
