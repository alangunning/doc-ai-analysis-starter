"""Simple wrapper around ``click-repl`` for an interactive shell."""

from __future__ import annotations

import click
from click_repl import repl
import typer
from typer.main import get_command

__all__ = ["interactive_shell"]


def interactive_shell(app: typer.Typer) -> None:
    """Start an interactive REPL for the given Typer application."""

    cmd = get_command(app)
    ctx = click.Context(cmd)
    repl(ctx, prompt_kwargs={"message": "doc-ai> "})

