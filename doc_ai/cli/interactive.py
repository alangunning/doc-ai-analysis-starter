"""Simple wrapper around ``click-repl`` for an interactive shell."""

from __future__ import annotations

from pathlib import Path

import click
from click_repl import repl
from prompt_toolkit.history import FileHistory
import typer
from typer.main import get_command

__all__ = ["interactive_shell"]


def interactive_shell(app: typer.Typer) -> None:
    """Start an interactive REPL for the given Typer application."""

    cmd = get_command(app)
    ctx = click.Context(cmd)
    history = FileHistory(Path.home() / ".doc-ai-history")
    repl(ctx, prompt=lambda: f"{Path.cwd().name}> ", history=history)

