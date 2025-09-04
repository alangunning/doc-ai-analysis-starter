from __future__ import annotations

import os
from pathlib import Path
import logging

import typer
from rich.table import Table
from rich.panel import Panel
from dotenv import set_key, dotenv_values

from doc_ai.logging import configure_logging
from .utils import load_env_defaults
from . import ENV_FILE, save_global_config, read_configs, console

logger = logging.getLogger(__name__)


app = typer.Typer(help="Show or update runtime configuration.")


def _set_pairs(ctx: typer.Context, pairs: list[str], use_global: bool) -> None:
    """Persist ``VAR=VALUE`` pairs to config sources."""
    force_global = use_global or any(
        p.split("=", 1)[0] == "interactive" for p in pairs
    )
    if force_global:
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
    verbose: bool | None = typer.Option(
        None, "--verbose", "-v", help="Shortcut for --log-level DEBUG"
    ),
    log_level: str | None = typer.Option(
        None, "--log-level", help="Logging level (e.g. INFO, DEBUG)"
    ),
    log_file: Path | None = typer.Option(
        None, "--log-file", help="Write logs to the given file"
    ),
    pairs: list[str] = typer.Option(None, "--set", metavar="VAR=VALUE"),
    global_scope: bool = typer.Option(
        False, "--global", help="Modify global config instead of project .env"
    ),
) -> None:
    """Configuration command group.

    Examples:
        doc-ai config --log-level DEBUG show
        doc-ai config show --log-file config.log
    """
    if ctx.obj is None:
        ctx.obj = {}
    if any(opt is not None for opt in (verbose, log_level, log_file)):
        level_name = "DEBUG" if verbose else log_level or logging.getLevelName(
            logging.getLogger().level
        )
        configure_logging(level_name, log_file)
        ctx.obj["verbose"] = logging.getLogger().level <= logging.DEBUG
        ctx.obj["log_level"] = level_name
        ctx.obj["log_file"] = log_file
    elif verbose is not None:
        ctx.obj["verbose"] = verbose
    if pairs:
        _set_pairs(ctx, pairs, global_scope)
        raise typer.Exit()


def _print_settings(ctx: typer.Context) -> None:
    logger.info("Current settings:")
    logger.info("  verbose: %s", ctx.obj.get("verbose"))
    defaults = load_env_defaults()
    defaults.setdefault("interactive", "true")
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


def set_defaults(
    ctx: typer.Context, pairs: list[str] = typer.Argument(..., metavar="VAR=VALUE")
) -> None:
    """Update runtime default options for the current session."""
    root = ctx.find_root()
    if root.default_map is None:
        root.default_map = {}
    for item in pairs:
        try:
            key, value = item.split("=", 1)
        except ValueError as exc:  # pragma: no cover - handled by typer
            raise typer.BadParameter("Use VAR=VALUE syntax") from exc
        root.default_map[key] = value
    table = Table("Option", "Value")
    for key, value in sorted(root.default_map.items()):
        table.add_row(key, str(value))
    console.print(Panel(table, title="Runtime defaults"))
