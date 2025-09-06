"""Scaffold new document type directories and prompt templates."""

from __future__ import annotations

import sys
import shutil
from pathlib import Path

import questionary
import typer

from .interactive import refresh_after, discover_doc_types_topics
from .utils import prompt_if_missing

app = typer.Typer(help="Scaffold a new document type with template prompts")

TEMPLATE_ANALYSIS = Path(".github/prompts/doc-analysis.analysis.prompt.yaml")
TEMPLATE_VALIDATE = Path(".github/prompts/validate-output.validate.prompt.yaml")
DATA_DIR = Path("data")


@app.command(
    "doc-type",
    help="Create a new document type directory under data/ with template prompts.",
)
@refresh_after  # type: ignore[misc]
def doc_type(
    ctx: typer.Context,
    name: str | None = typer.Argument(None, help="Document type"),
    description: str = typer.Option(
        "",
        "--description",
        help="Optional description or notes saved to description.txt",
    ),
) -> None:
    """Create a new document type directory populated with prompt templates."""
    if not TEMPLATE_ANALYSIS.exists() or not TEMPLATE_VALIDATE.exists():
        typer.echo("Template prompt files not found.", err=True)
        raise typer.Exit(code=1)

    name = prompt_if_missing(ctx, name, "Document type")
    if name is None:
        raise typer.BadParameter("Document type required")

    target_dir = DATA_DIR / name
    if target_dir.exists():
        typer.echo(f"Directory {target_dir} already exists", err=True)
        raise typer.Exit(code=1)
    target_dir.mkdir(parents=True, exist_ok=False)

    analysis_target = target_dir / f"{name}.analysis.prompt.yaml"
    validate_target = target_dir / "validate.prompt.yaml"
    shutil.copyfile(TEMPLATE_ANALYSIS, analysis_target)
    shutil.copyfile(TEMPLATE_VALIDATE, validate_target)

    if description:
        (target_dir / "description.txt").write_text(description + "\n")
    elif sys.stdin.isatty():
        # Interactively gather optional description or notes.
        typer.echo("Created new document type directory and prompt templates.")
        typer.echo(f"  {analysis_target}")
        typer.echo(f"  {validate_target}")
        typer.echo("Edit these files to customize prompts for your document type.")
        desc = typer.prompt(
            "Optional description or notes", default="", show_default=False
        ).strip()
        if desc:
            (target_dir / "description.txt").write_text(desc + "\n")
    else:
        typer.echo(f"Created {target_dir}")


@app.command("rename-doc-type", help="Rename a document type and its prompt files.")
@refresh_after  # type: ignore[misc]
def rename_doc_type(
    ctx: typer.Context,
    new: str,
    old: str | None = typer.Option(None, "--doc-type", help="Existing name"),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Automatically confirm the rename and skip the prompt",
    ),
) -> None:
    """Rename existing document type *old* to *new*."""

    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    old = old or cfg.get("default_doc_type")
    if old is None:
        doc_types, _ = discover_doc_types_topics()
        if doc_types:
            try:
                old = questionary.select(
                    "Select document type", choices=doc_types
                ).ask()
            except Exception:
                old = None
        old = prompt_if_missing(ctx, old, "Document type")
    if old is None:
        raise typer.BadParameter("Document type required")
    old_dir = DATA_DIR / old
    new_dir = DATA_DIR / new
    if not old_dir.exists():
        typer.echo(f"Directory {old_dir} does not exist", err=True)
        raise typer.Exit(code=1)
    if new_dir.exists():
        typer.echo(f"Directory {new_dir} already exists", err=True)
        raise typer.Exit(code=1)

    if sys.stdin.isatty() and not yes:
        if not typer.confirm(f"Rename {old} to {new}?", default=True):
            typer.echo("Aborted")
            return

    old_dir.rename(new_dir)
    for p in new_dir.glob(f"{old}.analysis*.prompt.yaml"):
        new_name = p.name.replace(f"{old}.analysis", f"{new}.analysis", 1)
        new_path = new_dir / new_name
        p.rename(new_path)
        desc_old = p.with_suffix(".description.txt")
        if desc_old.exists():
            desc_old.rename(new_path.with_suffix(".description.txt"))


@app.command("delete-doc-type", help="Delete a document type directory.")
@refresh_after  # type: ignore[misc]
def delete_doc_type(
    ctx: typer.Context,
    name: str | None = typer.Option(None, "--doc-type", help="Document type"),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Automatically confirm the deletion and skip the prompt",
    ),
) -> None:
    """Remove the document type directory named *name*."""

    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    name = name or cfg.get("default_doc_type")
    if name is None:
        doc_types, _ = discover_doc_types_topics()
        if doc_types:
            try:
                name = questionary.select(
                    "Select document type", choices=doc_types
                ).ask()
            except Exception:
                name = None
        name = prompt_if_missing(ctx, name, "Document type")
    if name is None:
        raise typer.BadParameter("Document type required")
    target_dir = DATA_DIR / name
    if not target_dir.exists():
        typer.echo(f"Directory {target_dir} does not exist", err=True)
        raise typer.Exit(code=1)

    if sys.stdin.isatty() and not yes:
        if not typer.confirm(f"Delete {target_dir}?", default=False):
            typer.echo("Aborted")
            return

    shutil.rmtree(target_dir)
