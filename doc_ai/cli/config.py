from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from dotenv import set_key

from .utils import load_env_defaults
from . import ENV_FILE, SETTINGS, console

app = typer.Typer(invoke_without_command=True, help="Show or update runtime configuration.")


@app.callback()
def config(
    verbose: bool = typer.Option(
        None, "--verbose/--no-verbose", help="Toggle verbose error output"
    ),
    set_vars: list[str] = typer.Option(
        None,
        "--set",
        help="Set VAR=VALUE pairs to update environment configuration",
        metavar="VAR=VALUE",
    ),
) -> None:
    """Show or update runtime configuration."""
    if verbose is not None:
        SETTINGS["verbose"] = verbose
    if set_vars:
        env_path = Path(ENV_FILE)
        env_path.touch(exist_ok=True)
        env_path.chmod(0o600)
        for item in set_vars:
            try:
                key, value = item.split("=", 1)
            except ValueError as exc:  # pragma: no cover - handled by typer
                raise typer.BadParameter("Use VAR=VALUE syntax") from exc
            os.environ[key] = value
            set_key(str(env_path), key, value, quote_mode="never")
            env_path.chmod(0o600)
    console.print("Current settings:")
    console.print(f"  verbose: {SETTINGS['verbose']}")
    defaults = load_env_defaults()
    if defaults:
        table = Table("Variable", "Current", "Default")
        for var, default in sorted(defaults.items()):
            table.add_row(var, os.getenv(var, "") or "-", default or "-")
        console.print(table)
