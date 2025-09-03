"""Reusable interactive shell with readline tab completion.

This module exposes `interactive_shell` for running a Typer/Click application in
an interactive loop. It also provides `get_completions` to allow unit tests or
other tooling to query available completions.
"""
from __future__ import annotations

import os
import shlex
import traceback
import atexit
from pathlib import Path
from typing import Callable

import click
import typer
from typer.main import get_command
from rich.console import Console

from .utils import load_env_defaults

__all__ = ["interactive_shell", "get_completions"]


def _complete_path(text: str, *, only_dirs: bool = False) -> list[str]:
    """Return filesystem path completions for ``text``.

    Parameters
    ----------
    text:
        Current token to complete.
    only_dirs:
        If ``True``, limit results to directories.
    """
    expanded = os.path.expanduser(text)
    directory, _, prefix = expanded.rpartition(os.sep)
    if directory:
        base = Path(directory or os.sep)
    else:
        base = Path(".")
    try:
        entries = list(base.iterdir())
    except OSError:
        return []
    results: list[str] = []
    for entry in entries:
        name = entry.name
        if not name.startswith(prefix):
            continue
        if only_dirs and not entry.is_dir():
            continue
        completion = os.path.join(directory, name) if directory else name
        if entry.is_dir():
            completion += os.sep
        results.append(completion)
    return results


def get_completions(app: typer.Typer, buffer: str, text: str) -> list[str]:
    """Return completion suggestions for the given buffer and token.

    Parameters
    ----------
    app:
        Typer application providing command definitions.
    buffer:
        Full current input line.
    text:
        Partial token to complete within ``buffer``.

    Returns
    -------
    list[str]
        Sorted list of suggested completions.

    Examples
    --------
    >>> from doc_ai.cli import app
    >>> get_completions(app, "co", "co")
    ['convert']
    """
    root = get_command(app)
    commands: dict[str, click.Command] = root.commands
    try:
        tokens = shlex.split(buffer)
    except ValueError:
        tokens = buffer.split()
    if buffer.endswith(" "):
        tokens.append("")
    suggestions: list[str] = []
    incomplete: str | None = None
    env_vars = set(os.environ) | set(load_env_defaults().keys())
    if tokens and tokens[-1].startswith("$"):
        incomplete = tokens[-1]
        prefix = incomplete[1:]
        suggestions = [f"${k}" for k in env_vars if k.startswith(prefix)]
    elif not tokens:
        suggestions = list(commands)
    elif tokens[0] == "cd":
        incomplete = tokens[1] if len(tokens) > 1 else ""
        suggestions = _complete_path(incomplete, only_dirs=True)
    elif len(tokens) == 1 and tokens[0].startswith("-"):
        incomplete = tokens[0]
        ctx = root.make_context(root.name, [], resilient_parsing=True)
        suggestions = [item.value for item in root.shell_complete(ctx, incomplete)]
    elif len(tokens) == 1:
        suggestions = [name for name in commands if name.startswith(tokens[0])]
        if not suggestions:
            incomplete = tokens[0]
            suggestions = _complete_path(incomplete)
    else:
        cmd = commands.get(tokens[0])
        if cmd:
            incomplete = tokens[-1]
            ctx = cmd.make_context(cmd.name, tokens[1:-1], resilient_parsing=True)
            suggestions = [item.value for item in cmd.shell_complete(ctx, incomplete)]
            if not suggestions and not incomplete.startswith("$"):
                suggestions = _complete_path(incomplete)
            if incomplete.startswith("$"):
                prefix = incomplete[1:]
                suggestions = [f"${k}" for k in env_vars if k.startswith(prefix)]
        else:
            incomplete = tokens[-1]
            suggestions = _complete_path(incomplete)
    if incomplete is not None and len(incomplete) > len(text):
        prefix = incomplete[: len(incomplete) - len(text)]
        suggestions = [s[len(prefix):] if s.startswith(prefix) else s for s in suggestions]
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

    Examples
    --------
    Run the library's own CLI in interactive mode::

        from doc_ai import cli
        cli.interactive_shell(cli.app)
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

        history_path = Path("~/.doc_ai_history").expanduser()
        try:
            readline.read_history_file(history_path)
        except Exception:
            pass
        atexit.register(lambda: readline.write_history_file(history_path))
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
            args = shlex.split(full_cmd)
        except ValueError as exc:
            console.print(f"[red]Parse error: {exc}[/red]")
            continue
        try:
            app(prog_name=prog_name, args=args)
        except SystemExit:
            pass
        except Exception as exc:  # pragma: no cover - runtime error display
            if verbose:
                traceback.print_exc()
            else:
                console.print(f"[red]{exc}[/red]")
