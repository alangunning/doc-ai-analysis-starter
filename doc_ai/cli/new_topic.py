# mypy: ignore-errors
"""Scaffold new topic prompt templates for existing document types."""

from __future__ import annotations

import sys
import shutil
import re
from pathlib import Path

import questionary
import typer

from .interactive import refresh_after, discover_doc_types_topics
from .utils import prompt_if_missing

app = typer.Typer(help="Scaffold a new analysis topic prompt for a document type")

TEMPLATE_TOPIC = Path(".github/prompts/doc-analysis.topic.prompt.yaml")
DATA_DIR = Path("data")


def _discover_topics(doc_type: str) -> list[str]:
    """Return sorted topics available under *doc_type*."""
    topics: set[str] = set()
    doc_dir = DATA_DIR / doc_type
    if not doc_dir.exists():
        return []
    for p in doc_dir.glob("analysis_*.prompt.yaml"):
        m = re.match(r"analysis_(.+)\.prompt\.yaml$", p.name)
        if m:
            topics.add(m.group(1))
    for p in doc_dir.glob(f"{doc_type}.analysis.*.prompt.yaml"):
        m = re.match(rf"{re.escape(doc_type)}\.analysis\.(.+)\.prompt\.yaml$", p.name)
        if m:
            topics.add(m.group(1))
    return sorted(topics)


@app.command(
    "topic",
    help="Create a new topic prompt under an existing document type directory.",
)
@refresh_after
def topic(
    ctx: typer.Context,
    topic: str | None = typer.Argument(None, help="Topic"),
    doc_type: str | None = typer.Option(None, "--doc-type", help="Document type"),
    description: str = typer.Option(
        "",
        "--description",
        help="Optional initial description saved next to the prompt",
    ),
) -> None:
    """Create a new topic prompt template for the given document type."""
    if not TEMPLATE_TOPIC.exists():
        typer.echo("Template prompt file not found.", err=True)
        raise typer.Exit(code=1)

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
    topic = prompt_if_missing(ctx, topic, "Topic")
    if topic is None:
        raise typer.BadParameter("Topic required")
    target_dir = DATA_DIR / doc_type
    if not target_dir.exists():
        typer.echo(f"Document type directory {target_dir} does not exist", err=True)
        raise typer.Exit(code=1)

    target_file = target_dir / f"{doc_type}.analysis.{topic}.prompt.yaml"
    if target_file.exists():
        typer.echo(f"Prompt file {target_file} already exists", err=True)
        raise typer.Exit(code=1)

    shutil.copyfile(TEMPLATE_TOPIC, target_file)

    if description:
        target_file.with_suffix(".description.txt").write_text(description + "\n")
    elif sys.stdin.isatty():
        typer.echo("Created new topic prompt template.")
        typer.echo(f"  {target_file}")
        desc = typer.prompt(
            "Optional initial description", default="", show_default=False
        ).strip()
        if desc:
            target_file.with_suffix(".description.txt").write_text(desc + "\n")
    else:
        typer.echo(f"Created {target_file}")


@app.command("rename-topic", help="Rename a topic prompt for a document type.")
@refresh_after
def rename_topic(
    ctx: typer.Context,
    old: str | None = typer.Argument(None, help="Existing topic"),
    new: str | None = typer.Argument(None, help="New topic name"),
    doc_type: str | None = typer.Option(None, "--doc-type", help="Document type"),
) -> None:
    """Rename topic *old* to *new* under *doc_type*."""

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
    topics = _discover_topics(doc_type)
    old = old or cfg.get("default_topic")
    if old is None:
        if topics:
            try:
                old = questionary.select("Select topic", choices=topics).ask()
            except Exception:
                old = None
        old = prompt_if_missing(ctx, old, "Topic")
    if old is None:
        raise typer.BadParameter("Topic required")
    new = prompt_if_missing(ctx, new, "New topic name")
    if new is None:
        raise typer.BadParameter("New topic name required")
    target_dir = DATA_DIR / doc_type
    if not target_dir.exists():
        typer.echo(f"Document type directory {target_dir} does not exist", err=True)
        raise typer.Exit(code=1)

    old_file = target_dir / f"{doc_type}.analysis.{old}.prompt.yaml"
    new_file = target_dir / f"{doc_type}.analysis.{new}.prompt.yaml"
    if not old_file.exists():
        typer.echo(f"Prompt file {old_file} does not exist", err=True)
        raise typer.Exit(code=1)
    if new_file.exists():
        typer.echo(f"Prompt file {new_file} already exists", err=True)
        raise typer.Exit(code=1)

    if sys.stdin.isatty():
        if not typer.confirm(f"Rename topic {old} to {new}?", default=True):
            typer.echo("Aborted")
            return

    old_file.rename(new_file)
    desc = old_file.with_suffix(".description.txt")
    if desc.exists():
        desc.rename(new_file.with_suffix(".description.txt"))


@app.command("delete-topic", help="Delete a topic prompt from a document type.")
@refresh_after
def delete_topic(
    ctx: typer.Context,
    topic: str | None = typer.Argument(None, help="Topic"),
    doc_type: str | None = typer.Option(None, "--doc-type", help="Document type"),
) -> None:
    """Delete the topic prompt *topic* under *doc_type*."""

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
    topics = _discover_topics(doc_type)
    topic = topic or cfg.get("default_topic")
    if topic is None:
        if topics:
            try:
                topic = questionary.select("Select topic", choices=topics).ask()
            except Exception:
                topic = None
        topic = prompt_if_missing(ctx, topic, "Topic")
    if topic is None:
        raise typer.BadParameter("Topic required")
    target_dir = DATA_DIR / doc_type
    if not target_dir.exists():
        typer.echo(f"Document type directory {target_dir} does not exist", err=True)
        raise typer.Exit(code=1)

    target_file = target_dir / f"{doc_type}.analysis.{topic}.prompt.yaml"
    if not target_file.exists():
        typer.echo(f"Prompt file {target_file} does not exist", err=True)
        raise typer.Exit(code=1)

    if sys.stdin.isatty():
        if not typer.confirm(f"Delete topic {topic}?", default=False):
            typer.echo("Aborted")
            return

    target_file.unlink()
    desc = target_file.with_suffix(".description.txt")
    if desc.exists():
        desc.unlink()
