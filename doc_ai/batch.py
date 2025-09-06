from __future__ import annotations

from pathlib import Path

import click
import typer
from click.exceptions import Exit as ClickExit
from click_repl.utils import (  # type: ignore[import-untyped]
    dispatch_repl_commands,
    handle_internal_commands,
    split_arg_string,
)
from click_repl.exceptions import CommandLineParserError  # type: ignore[import-untyped]

from doc_ai import plugins


def _parse_command(command: str) -> list[str] | None:
    """Parse a command line similar to the REPL parser."""
    if dispatch_repl_commands(command):
        return None
    result = handle_internal_commands(command)
    if isinstance(result, str):
        click.echo(result)
        return None
    try:
        parts = split_arg_string(command, posix=False)
        cleaned = []
        for part in parts:
            if len(part) >= 2 and part[0] == part[-1] and part[0] in {'"', "'"}:
                cleaned.append(part[1:-1])
            else:
                cleaned.append(part)
        if cleaned and cleaned[0] in plugins.iter_repl_commands():
            plugins.iter_repl_commands()[cleaned[0]](cleaned[1:])
            return None
        return cleaned
    except ValueError as exc:
        raise CommandLineParserError(str(exc)) from exc


def run_batch(ctx: click.Context, path: Path) -> None:
    """Execute commands from *path* before starting the REPL."""
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            args = _parse_command(line)
        except CommandLineParserError as exc:
            err = click.ClickException(f"{path}:{lineno}: {exc}")
            err.exit_code = 1
            raise err from exc
        if args is None:
            continue
        sub_ctx: click.Context | None = None
        try:
            sub_ctx = ctx.command.make_context(
                ctx.command.name,
                args,
                obj=ctx.obj,
                default_map=ctx.default_map,
            )
            ctx.command.invoke(sub_ctx)
        except click.ClickException as exc:
            err = click.ClickException(
                f"{path}:{lineno}: {exc.format_message()}"
            )
            err.exit_code = exc.exit_code
            raise err from exc
        except ClickExit as exc:
            raise typer.Exit(exc.exit_code)
        finally:
            if sub_ctx is not None:
                ctx.default_map = sub_ctx.default_map
