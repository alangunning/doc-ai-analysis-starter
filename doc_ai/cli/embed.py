from __future__ import annotations

from pathlib import Path
import logging

import typer

from . import build_vector_store
from .utils import resolve_bool, resolve_int

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
) -> None:
    """Generate embeddings for Markdown files.

    Examples:
        doc-ai embed docs/
    """
    if ctx.obj is None:
        ctx.obj = {}
    cfg = ctx.obj.get("config", {})
    fail_fast = resolve_bool(ctx, "fail_fast", fail_fast, cfg, "FAIL_FAST")
    workers = resolve_int(ctx, "workers", workers, cfg, "WORKERS")
    build_vector_store(source, fail_fast=fail_fast, workers=workers)
