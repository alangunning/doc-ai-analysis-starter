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
import collections.abc as cabc
import typing as t

import click
from click.core import ParameterSource
from click.shell_completion import split_arg_string
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


# Copied from Click's shell completion utilities (BSD-3-Clause license)
# to avoid relying on its private API.
def _start_of_option(ctx: click.Context, value: str) -> bool:
    """Return True if *value* looks like the start of an option."""
    if not value:
        return False
    return value[0] in ctx._opt_prefixes


def _is_incomplete_option(
    ctx: click.Context, args: list[str], param: click.Parameter
) -> bool:
    """Check if *param* is an option waiting for a value."""
    if not isinstance(param, click.Option):
        return False
    if param.is_flag or param.count:
        return False
    last_option = None
    for index, arg in enumerate(reversed(args)):
        if index + 1 > param.nargs:
            break
        if _start_of_option(ctx, arg):
            last_option = arg
    return last_option is not None and last_option in param.opts


def _is_incomplete_argument(ctx: click.Context, param: click.Parameter) -> bool:
    """Check if *param* is an argument that can accept more values."""
    if not isinstance(param, click.Argument):
        return False
    assert param.name is not None
    value = ctx.params.get(param.name)
    return (
        param.nargs == -1
        or ctx.get_parameter_source(param.name) is not ParameterSource.COMMANDLINE
        or (
            param.nargs > 1
            and isinstance(value, (tuple, list))
            and len(value) < param.nargs
        )
    )


def _resolve_context(
    cli: click.Command,
    ctx_args: cabc.MutableMapping[str, t.Any],
    prog_name: str,
    args: list[str],
) -> click.Context:
    """Resolve a context for *args* starting from *cli*."""
    ctx_args["resilient_parsing"] = True
    with cli.make_context(prog_name, args.copy(), **ctx_args) as ctx:
        args = ctx._protected_args + ctx.args
        while args:
            command = ctx.command
            if isinstance(command, click.Group):
                if not command.chain:
                    name, cmd, args = command.resolve_command(ctx, args)
                    if cmd is None:
                        return ctx
                    with cmd.make_context(
                        name, args, parent=ctx, resilient_parsing=True
                    ) as sub_ctx:
                        ctx = sub_ctx
                        args = ctx._protected_args + ctx.args
                else:
                    sub_ctx = ctx
                    while args:
                        name, cmd, args = command.resolve_command(ctx, args)
                        if cmd is None:
                            return ctx
                        with cmd.make_context(
                            name,
                            args,
                            parent=ctx,
                            allow_extra_args=True,
                            allow_interspersed_args=False,
                            resilient_parsing=True,
                        ) as sub_sub_ctx:
                            sub_ctx = sub_sub_ctx
                            args = sub_ctx.args
                    ctx = sub_ctx
                    args = [*sub_ctx._protected_args, *sub_ctx.args]
            else:
                break
    return ctx


def _resolve_incomplete(
    ctx: click.Context, args: list[str], incomplete: str
) -> tuple[click.Command | click.Parameter, str]:
    """Find the Click object responsible for *incomplete*."""
    if incomplete == "=":
        incomplete = ""
    elif "=" in incomplete and _start_of_option(ctx, incomplete):
        name, _, incomplete = incomplete.partition("=")
        args.append(name)
    if "--" not in args and _start_of_option(ctx, incomplete):
        return ctx.command, incomplete
    params = ctx.command.get_params(ctx)
    for param in params:
        if _is_incomplete_option(ctx, args, param):
            return param, incomplete
    for param in params:
        if _is_incomplete_argument(ctx, param):
            return param, incomplete
    return ctx.command, incomplete

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
