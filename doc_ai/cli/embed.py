from __future__ import annotations

from pathlib import Path

import typer

from . import build_vector_store

app = typer.Typer(invoke_without_command=True, help="Generate embeddings for Markdown files.")


@app.callback()
def embed(
    ctx: typer.Context,
    source: Path = typer.Argument(..., help="Directory containing Markdown files"),
    fail_fast: bool = typer.Option(
        False, "--fail-fast", help="Abort immediately on the first HTTP error"
    ),
) -> None:
    """Generate embeddings for Markdown files."""
    build_vector_store(source, fail_fast=fail_fast)
