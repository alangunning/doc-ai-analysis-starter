from __future__ import annotations

"""Utilities for showing and editing prompt definition files."""

from pathlib import Path
import os
import shlex
import shutil
import subprocess

import typer

DATA_DIR = Path("data")


def resolve_prompt_path(doc_type: str, topic: str | None) -> Path:
    """Return the prompt file path for a document type and optional topic."""
    base_dir = DATA_DIR / doc_type
    if not base_dir.is_dir():
        raise typer.BadParameter(f"Unknown document type '{doc_type}'")
    topic_name = topic or "analysis"
    candidates = [
        base_dir / f"{doc_type}.{topic_name}.prompt.yaml",
        base_dir / f"{topic_name}.prompt.yaml",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise typer.BadParameter(
        f"Prompt file not found for topic '{topic_name}' in {base_dir}"
    )


def show_prompt(doc_type: str, topic: str | None) -> str:
    """Return the contents of the prompt file."""
    path = resolve_prompt_path(doc_type, topic)
    return path.read_text()


def edit_prompt(doc_type: str, topic: str | None) -> None:
    """Launch an editor for the prompt file.

    Uses shlex.split so editors with arguments are handled properly.
    """
    path = resolve_prompt_path(doc_type, topic)
    editor = os.environ.get("EDITOR")
    if not editor:
        for candidate in ("vi", "nano"):
            if shutil.which(candidate):
                editor = candidate
                break
        else:
            editor = "vi"
    subprocess.run(shlex.split(editor) + [str(path)], check=True)
