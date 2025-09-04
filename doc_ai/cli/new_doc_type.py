from __future__ import annotations

"""Scaffold new document type directories and prompt templates."""

import sys
import shutil
from pathlib import Path

import typer

app = typer.Typer(help="Scaffold a new document type with template prompts")

TEMPLATE_ANALYSIS = Path(".github/prompts/doc-analysis.analysis.prompt.yaml")
TEMPLATE_VALIDATE = Path(".github/prompts/validate-output.validate.prompt.yaml")
DATA_DIR = Path("data")


@app.command("doc-type")
def doc_type(name: str) -> None:
    """Create a new document type directory populated with prompt templates."""
    if not TEMPLATE_ANALYSIS.exists() or not TEMPLATE_VALIDATE.exists():
        typer.echo("Template prompt files not found.", err=True)
        raise typer.Exit(code=1)

    target_dir = DATA_DIR / name
    if target_dir.exists():
        typer.echo(f"Directory {target_dir} already exists", err=True)
        raise typer.Exit(code=1)
    target_dir.mkdir(parents=True, exist_ok=False)

    analysis_target = target_dir / f"{name}.analysis.prompt.yaml"
    validate_target = target_dir / "validate.prompt.yaml"
    shutil.copyfile(TEMPLATE_ANALYSIS, analysis_target)
    shutil.copyfile(TEMPLATE_VALIDATE, validate_target)

    if sys.stdin.isatty():
        # Interactively gather optional description or notes.
        typer.echo("Created new document type directory and prompt templates.")
        typer.echo(f"  {analysis_target}")
        typer.echo(f"  {validate_target}")
        typer.echo("Edit these files to customize prompts for your document type.")
        typer.prompt("Optional description or notes", default="", show_default=False)
    else:
        typer.echo(f"Created {target_dir}")
