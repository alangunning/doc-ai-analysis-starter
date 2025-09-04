from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.table import Table
from dotenv import set_key, dotenv_values

from .utils import load_env_defaults
from . import ENV_FILE, console, save_global_config, read_configs


app = typer.Typer(help="Show or update runtime configuration.")


def _set_pairs(ctx: typer.Context, pairs: list[str], use_global: bool) -> None:
    """Persist ``VAR=VALUE`` pairs to config sources."""
    if use_global:
        cfg = dict(ctx.obj.get("global_config", {}))
        for item in pairs:
            try:
                key, value = item.split("=", 1)
            except ValueError as exc:  # pragma: no cover - handled by typer
                raise typer.BadParameter("Use VAR=VALUE syntax") from exc
            os.environ[key] = value
            cfg[key] = value
        save_global_config(cfg)
        ctx.obj["global_config"] = cfg
    else:
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
    global_cfg, _env_vals, merged = read_configs()
    ctx.obj.update({"global_config": global_cfg, "config": merged})


@app.callback()
def config(
    ctx: typer.Context,
    verbose: bool = typer.Option(None, "--verbose/--no-verbose"),
    pairs: list[str] = typer.Option(None, "--set", metavar="VAR=VALUE"),
    global_scope: bool = typer.Option(
        False, "--global", help="Modify global config instead of project .env"
    ),
) -> None:
    """Configuration command group."""
    if verbose is not None:
        ctx.obj["verbose"] = verbose
    if pairs:
        _set_pairs(ctx, pairs, global_scope)
        raise typer.Exit()


def _print_settings(ctx: typer.Context) -> None:
    console.print("Current settings:")
    console.print(f"  verbose: {ctx.obj.get('verbose')}")
    defaults = load_env_defaults()
    for key in os.environ:
        if key.startswith("MODEL_PRICE_") and key not in defaults:
            defaults[key] = None
    global_cfg = ctx.obj.get("global_config", {})
    env_cfg = dotenv_values(ENV_FILE)
    keys = set(defaults) | set(global_cfg) | set(env_cfg)
    for key in os.environ:
        if key in global_cfg or key in env_cfg or key.startswith("MODEL_PRICE_"):
            keys.add(key)
    if keys:
        table = Table("Variable", "Effective", ".env", "Global", "Default")
        for var in sorted(keys):
            table.add_row(
                var,
                os.getenv(var, "") or "-",
                env_cfg.get(var, "-") or "-",
                global_cfg.get(var, "-") or "-",
                defaults.get(var, "-") or "-",
            )
        console.print(table)


@app.command()
def show(ctx: typer.Context) -> None:
    """Display current settings."""
    _print_settings(ctx)


@app.command("set")
def set_value(
    ctx: typer.Context,
    pairs: list[str] = typer.Argument(..., metavar="VAR=VALUE"),
    global_scope: bool = typer.Option(
        False, "--global", help="Modify global config instead of project .env"
    ),
) -> None:
    """Update environment configuration."""
    _set_pairs(ctx, pairs, global_scope)
