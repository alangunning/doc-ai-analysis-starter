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

    Resolves ``$EDITOR`` using :func:`shutil.which` and falls back to a safe
    default (``vi`` or ``nano``) when the variable is unset, invalid, or points
    to a non-existent command. Values containing path separators or shell
    metacharacters are ignored to avoid command injection vulnerabilities.
    """

    path = resolve_prompt_path(doc_type, topic)

    invalid_chars = set(";&|$><`")
    # Disallow path separators to ensure only simple command names are used.
    path_seps = {os.sep}
    if os.altsep:
        path_seps.add(os.altsep)

    editor_cmd: list[str] | None = None
    editor_env = os.environ.get("EDITOR")

    if editor_env and not any(ch in editor_env for ch in invalid_chars.union(path_seps)):
        parts = shlex.split(editor_env)
        if parts:
            resolved = shutil.which(parts[0])
            if resolved:
                editor_cmd = [resolved, *parts[1:]]

    if editor_cmd is None:
        for candidate in ("vi", "nano"):
            resolved = shutil.which(candidate)
            if resolved:
                editor_cmd = [resolved]
                break
        else:
            editor_cmd = ["vi"]

    subprocess.run(editor_cmd + [str(path)], check=True)
