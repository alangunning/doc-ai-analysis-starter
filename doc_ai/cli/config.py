from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.table import Table
from dotenv import set_key

from .utils import load_env_defaults
from . import ENV_FILE, SETTINGS, console


app = typer.Typer(help="Show or update runtime configuration.")


def _set_pairs(pairs: list[str]) -> None:
    """Persist ``VAR=VALUE`` pairs to the .env file."""
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


@app.callback()
def config(
    verbose: bool = typer.Option(None, "--verbose/--no-verbose"),
    set: list[str] = typer.Option(None, "--set", metavar="VAR=VALUE"),
) -> None:
    """Configuration command group."""
    if verbose is not None:
        SETTINGS["verbose"] = verbose
    if set:
        _set_pairs(set)
        raise typer.Exit()


def _print_settings() -> None:
    console.print("Current settings:")
    console.print(f"  verbose: {SETTINGS['verbose']}")
    defaults = load_env_defaults()
    for key in os.environ:
        if key.startswith("MODEL_PRICE_") and key not in defaults:
            defaults[key] = None
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
    _set_pairs(pairs)
