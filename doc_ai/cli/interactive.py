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
from click.shell_completion import (
    _resolve_context,
    _resolve_incomplete,
    split_arg_string,
)
import typer
from typer.main import get_command
from rich.console import Console

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
    """Return completion suggestions for the given buffer and text.

    Uses Click's ``shell_completion`` helpers to resolve the current
    command context and delegate option and argument completions. A custom
    fallback completes filesystem paths when Click requests file or
    directory completion or for built-in commands like ``cd``.
    """
    root = get_command(app)
    commands: dict[str, click.Command] = root.commands
    tokens = split_arg_string(buffer)
    if buffer.endswith(" "):
        tokens.append("")
    suggestions: list[str] = []
    incomplete = ""

    if not tokens:
        ctx = click.Context(root)
        suggestions = [item.value for item in root.shell_complete(ctx, "")]
    elif tokens[0] == "cd":
        incomplete = tokens[1] if len(tokens) > 1 else ""
        suggestions = _complete_path(incomplete, only_dirs=True)
    elif len(tokens) == 1:
        ctx = click.Context(root)
        items = root.shell_complete(ctx, tokens[0])
        if items:
            suggestions = [item.value for item in items]
        else:
            incomplete = tokens[0]
            suggestions = _complete_path(incomplete)
    elif tokens[0] not in commands:
        incomplete = tokens[-1]
        suggestions = _complete_path(incomplete)
    else:
        ctx = _resolve_context(root, {}, root.name or "", tokens[:-1])
        obj, incomplete = _resolve_incomplete(ctx, tokens[:-1], tokens[-1])
        items = obj.shell_complete(ctx, incomplete)
        if items:
            types = {getattr(item, "type", None) for item in items}
            if types <= {"file", "dir"}:
                suggestions = _complete_path(
                    incomplete, only_dirs=types == {"dir"}
                )
            else:
                suggestions = [item.value for item in items]
        else:
            suggestions = _complete_path(incomplete)

    if incomplete and len(incomplete) > len(text):
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
