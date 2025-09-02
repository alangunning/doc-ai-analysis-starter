"""Reusable interactive shell with readline tab completion.

This module exposes `interactive_shell` for running a Typer/Click application in
an interactive loop. It also provides `get_completions` to allow unit tests or
other tooling to query available completions.
"""
from __future__ import annotations

import os
import shlex
import traceback
from pathlib import Path
from typing import Callable

import click
import typer
from typer.main import get_command
from rich.console import Console

__all__ = ["interactive_shell", "get_completions"]


def get_completions(app: typer.Typer, buffer: str, text: str) -> list[str]:
    """Return completion suggestions for the given buffer and text."""
    root = get_command(app)
    commands: dict[str, click.Command] = root.commands
    try:
        tokens = shlex.split(buffer)
    except ValueError:
        tokens = buffer.split()
    if buffer.endswith(" "):
        tokens.append("")
    suggestions: list[str] = []
    if not tokens:
        suggestions = list(commands)
    elif len(tokens) == 1:
        suggestions = [name for name in commands if name.startswith(tokens[0])]
    else:
        cmd = commands.get(tokens[0])
        if cmd:
            incomplete = tokens[-1]
            ctx = click.Context(cmd, info_name=cmd.name, resilient_parsing=True)
            suggestions = [item.value for item in cmd.shell_complete(ctx, incomplete)]
    return sorted(suggestions)


def interactive_shell(
    app: typer.Typer,
    *,
    prog_name: str = "cli.py",
    console: Console | None = None,
    print_banner: Callable[[], None] | None = None,
    verbose: bool = False,
) -> None:
    """Run an interactive CLI loop for the given Typer application.

    Parameters
    ----------
    app:
        The Typer application to execute.
    prog_name:
        Program name used when invoking the app.
    console:
        Optional rich console for output.
    print_banner:
        Callback to print a startup banner before the shell prompt appears.
    verbose:
        If ``True``, include ``--verbose`` in executed commands and show full
        tracebacks on errors.

    The loop provides readline-based tab completion for commands and options and
    supports simple built-in commands like ``cd`` and ``exit``.
    """
    console = console or Console()
    try:  # pragma: no cover - depends on system readline availability
        import readline  # type: ignore
    except Exception:  # pragma: no cover - platform-specific
        readline = None
    if readline is not None:  # pragma: no cover - interactive only
        def completer(text: str, state: int) -> str | None:
            options = get_completions(app, readline.get_line_buffer(), text)
            return options[state] if state < len(options) else None

        try:
            readline.set_completer(completer)
            readline.parse_and_bind("tab: complete")
        except Exception:
            pass
    if print_banner:
        try:
            print_banner()
            app(prog_name=prog_name, args=["--help"])
        except SystemExit:
            pass
    while True:
        try:
            command = input("> ").strip()
        except (EOFError, KeyboardInterrupt):  # pragma: no cover - user exits
            break
        if not command:
            continue
        if command.lower() in {"exit", "quit"}:
            break
        if command.startswith("cd"):
            parts = command.split(maxsplit=1)
            target = Path(parts[1]).expanduser() if len(parts) > 1 else Path.home()
            try:
                os.chdir(target)
            except OSError as exc:
                console.print(f"[red]{exc}[/red]")
            continue
        full_cmd = command
        if verbose:
            full_cmd += " --verbose"
        try:
            app(prog_name=prog_name, args=shlex.split(full_cmd))
        except SystemExit:
            pass
        except Exception as exc:  # pragma: no cover - runtime error display
            if verbose:
                traceback.print_exc()
            else:
                console.print(f"[red]{exc}[/red]")
