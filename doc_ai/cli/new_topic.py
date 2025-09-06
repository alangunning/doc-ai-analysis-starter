"""Scaffold new topic prompt templates for existing document types."""

from __future__ import annotations

import sys
import shutil
from pathlib import Path

import typer

from .interactive import refresh_completer

app = typer.Typer(help="Scaffold a new analysis topic prompt for a document type")

TEMPLATE_TOPIC = Path(".github/prompts/doc-analysis.topic.prompt.yaml")
DATA_DIR = Path("data")


@app.command(
    "topic",
    help="Create a new topic prompt under an existing document type directory.",
)
def topic(doc_type: str, topic: str) -> None:
    """Create a new topic prompt template for the given document type."""
    if not TEMPLATE_TOPIC.exists():
        typer.echo("Template prompt file not found.", err=True)
        raise typer.Exit(code=1)

    target_dir = DATA_DIR / doc_type
    if not target_dir.exists():
        typer.echo(f"Document type directory {target_dir} does not exist", err=True)
        raise typer.Exit(code=1)

    target_file = target_dir / f"{doc_type}.analysis.{topic}.prompt.yaml"
    if target_file.exists():
        typer.echo(f"Prompt file {target_file} already exists", err=True)
        raise typer.Exit(code=1)

    shutil.copyfile(TEMPLATE_TOPIC, target_file)

    if sys.stdin.isatty():
        typer.echo("Created new topic prompt template.")
        typer.echo(f"  {target_file}")
        typer.prompt("Optional initial description", default="", show_default=False)
    else:
        typer.echo(f"Created {target_file}")
    refresh_completer()
