from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.table import Table
from dotenv import set_key

from .utils import load_env_defaults
from . import ENV_FILE, SETTINGS, console


app = typer.Typer(help="Show or update runtime configuration.")


@app.callback()
def config(verbose: bool = typer.Option(None, "--verbose/--no-verbose")) -> None:
    """Configuration command group."""
    if verbose is not None:
        SETTINGS["verbose"] = verbose


def _print_settings() -> None:
    console.print("Current settings:")
    console.print(f"  verbose: {SETTINGS['verbose']}")
    defaults = load_env_defaults()
    if defaults:
        table = Table("Variable", "Current", "Default")
        for var, default in sorted(defaults.items()):
            table.add_row(var, os.getenv(var, "") or "-", default or "-")
        console.print(table)


@app.command()
def show() -> None:
    """Display current settings."""
    _print_settings()


@app.command()
def set(pairs: list[str] = typer.Argument(..., metavar="VAR=VALUE")) -> None:
    """Update environment configuration."""
    env_path = Path(ENV_FILE)
    env_path.touch(exist_ok=True)
    env_path.chmod(0o600)
    for item in pairs:
        try:
            key, value = item.split("=", 1)
        except ValueError as exc:  # pragma: no cover - handled by typer
            raise typer.BadParameter("Use VAR=VALUE syntax") from exc
        os.environ[key] = value
        set_key(str(env_path), key, value, quote_mode="never")
        env_path.chmod(0o600)
    _print_settings()
