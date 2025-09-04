"""Interactive REPL helper for the Doc AI CLI."""

from __future__ import annotations

from pathlib import Path
import os
import re

import click
from click_repl import repl, ClickCompleter
from click_repl.utils import (
    dispatch_repl_commands,
    handle_internal_commands,
    split_arg_string,
)
from click_repl.exceptions import CommandLineParserError
from click.exceptions import Exit as ClickExit
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, Completion, WordCompleter
import typer
from typer.main import get_command

__all__ = ["interactive_shell", "run_batch", "DocAICompleter"]


class DocAICompleter(Completer):
    """Completer that hides sensitive environment variables."""

    def __init__(self, cli: click.BaseCommand, ctx: click.Context) -> None:
        self._click = ClickCompleter(cli, ctx)
        env_words = [
            f"${name}"
            for name in os.environ
            if not re.search(r"TOKEN|SECRET|PASSWORD", name, re.IGNORECASE)
        ]
        self._env = WordCompleter(env_words, ignore_case=True)

    def get_completions(self, document, complete_event=None):  # type: ignore[override]
        if document.text_before_cursor.startswith("$"):
            yield from self._env.get_completions(document, complete_event)
        else:
            yield from self._click.get_completions(document, complete_event)


def _parse_command(command: str) -> list[str] | None:
    """Parse a command line similar to click-repl's REPL parser."""
    if dispatch_repl_commands(command):
        return None
    result = handle_internal_commands(command)
    if isinstance(result, str):
        click.echo(result)
        return None
    try:
        return split_arg_string(command, posix=False)
    except ValueError as exc:  # pragma: no cover - handled by caller
        raise CommandLineParserError(str(exc)) from exc


def run_batch(ctx: click.Context, path: Path) -> None:
    """Execute commands from *path* before starting the REPL."""
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        args = _parse_command(line)
        if args is None:
            continue
        sub_ctx = ctx.command.make_context(
            ctx.command.name,
            args,
            obj=ctx.obj,
            default_map=ctx.default_map,
        )
        try:
            ctx.command.invoke(sub_ctx)
        except click.ClickException:
            raise
        except ClickExit as exc:
            raise typer.Exit(exc.exit_code)
        finally:
            ctx.default_map = sub_ctx.default_map


def interactive_shell(app: typer.Typer, init: Path | None = None) -> None:
    """Start an interactive REPL for the given Typer application."""

    cmd = get_command(app)
    ctx = click.Context(cmd)
    if init is not None:
        run_batch(ctx, init)
    history = FileHistory(Path.home() / ".doc-ai-history")
    prompt_kwargs = {
        "history": history,
        "message": "doc-ai>",
        "completer": DocAICompleter(cmd, ctx),
    }
    repl(ctx, prompt_kwargs=prompt_kwargs)
