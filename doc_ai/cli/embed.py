from __future__ import annotations

from pathlib import Path

import typer

from . import build_vector_store
from .utils import prompt_if_missing, resolve_bool, resolve_int

app = typer.Typer(
    invoke_without_command=True, help="Generate embeddings for Markdown files."
)


@app.callback()
def embed(
    ctx: typer.Context,
    source: Path | None = typer.Argument(
        None, help="Directory containing Markdown files"
    ),
    fail_fast: bool = typer.Option(
        False, "--fail-fast", help="Abort immediately on the first HTTP error"
    ),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of worker threads"),
) -> None:
    """Generate embeddings for Markdown files.

    Examples:
        doc-ai embed docs/
    """
    if ctx.obj is None:
        ctx.obj = {}
    cfg = ctx.obj.get("config", {})
    src_val = prompt_if_missing(
        ctx,
        str(source) if source is not None else None,
        "Directory containing Markdown files",
    )
    if src_val is None:
        raise typer.BadParameter("Missing argument 'source'")
    source = Path(src_val)
    fail_fast = resolve_bool(ctx, "fail_fast", fail_fast, cfg, "FAIL_FAST")
    workers = resolve_int(ctx, "workers", workers, cfg, "WORKERS")
    build_vector_store(source, fail_fast=fail_fast, workers=workers)
