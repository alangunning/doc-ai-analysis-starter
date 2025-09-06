from __future__ import annotations

import os
from pathlib import Path
import logging
import sys

import typer
from rich.table import Table
from rich.panel import Panel
from dotenv import set_key, dotenv_values
import questionary

from .utils import get_logging_options, load_env_defaults, prompt_if_missing
from . import ENV_FILE, save_global_config, read_configs, console
from .interactive import refresh_completer, SAFE_ENV_VARS_ENV, _parse_allow_deny

TRUE_SET = {"1", "true", "yes"}
FALSE_SET = {"0", "false", "no"}

# Known configuration keys and booleans for validation
_defaults = load_env_defaults()
BOOLEAN_KEYS = {
    "FAIL_FAST",
    "VERBOSE",
    "INTERACTIVE",
    "ASK",
    "FORCE",
    "SHOW_COST",
    "ESTIMATE",
    "REQUIRE_STRUCTURED",
    "DRY_RUN",
    "YES",
    "DOC_AI_BANNER",
    "DOC_AI_ALLOW_SHELL",
} | {
    k
    for k, v in _defaults.items()
    if isinstance(v, str) and v.lower() in TRUE_SET | FALSE_SET
}

KNOWN_KEYS = set(_defaults) | {
    "MODEL",
    "BASE_MODEL_URL",
    "REQUIRE_STRUCTURED",
    "SHOW_COST",
    "ESTIMATE",
    "FORCE",
    "FAIL_FAST",
    "OUTPUT_FORMATS",
    "WORKERS",
    "DEST",
    "OVERWRITE",
    "DRY_RUN",
    "YES",
    "RESUME_FROM",
    "ASK",
    "VALIDATE_MODEL",
    "VALIDATE_BASE_MODEL_URL",
    "LOG_LEVEL",
    "LOG_FILE",
    "VERBOSE",
    "DOC_AI_BANNER",
    "DOC_AI_ALLOW_SHELL",
    "DOC_AI_HISTORY_FILE",
    "INTERACTIVE",
}

logger = logging.getLogger(__name__)


app = typer.Typer(help="Show or update runtime configuration.")

safe_env_app = typer.Typer(
    help=(
        "Manage environment variable exposure in the REPL. Only a minimal set "
        "like PATH and HOME is exposed by default; use allow/deny lists to "
        "change what variables are available."
    )
)
app.add_typer(safe_env_app, name="safe-env")


def _read_safe_env(ctx: typer.Context) -> tuple[set[str], set[str]]:
    cfg = ctx.obj.get("global_config", {}) if ctx.obj else {}
    raw = cfg.get(SAFE_ENV_VARS_ENV)
    return _parse_allow_deny(raw)


def _write_safe_env(ctx: typer.Context, allow: set[str], deny: set[str]) -> None:
    cfg = dict(ctx.obj.get("global_config", {}))
    parts = list(sorted(allow)) + [f"-{d}" for d in sorted(deny)]
    if parts:
        cfg[SAFE_ENV_VARS_ENV] = ",".join(parts)
    else:
        cfg.pop(SAFE_ENV_VARS_ENV, None)
    save_global_config(cfg)
    ctx.obj["global_config"] = cfg
    refresh_completer()


@safe_env_app.command("list")
def list_safe_env(ctx: typer.Context) -> None:
    """Show allowed and denied environment variable names."""
    allow, deny = _read_safe_env(ctx)
    table = Table("Allowed", "Denied")
    rows = max(len(allow), len(deny))
    allow_list = sorted(allow)
    deny_list = sorted(deny)
    for i in range(rows):
        a = allow_list[i] if i < len(allow_list) else ""
        d = deny_list[i] if i < len(deny_list) else ""
        table.add_row(a, d)
    console.print(table)


@safe_env_app.command("add")
def add_safe_env(
    ctx: typer.Context, names: list[str] | None = typer.Argument(None, metavar="NAME")
) -> None:
    """Allow environment variables (prefix with '-' to deny)."""
    allow, deny = _read_safe_env(ctx)
    items = list(names or [])
    if not items:
        name = prompt_if_missing(ctx, None, "Environment variable name")
        if name is None:
            raise typer.BadParameter("NAME required")
        items = [name]
    for raw in items:
        a, d = _parse_allow_deny(raw)
        allow |= a
        deny |= d
    _write_safe_env(ctx, allow, deny)


@safe_env_app.command("remove")
def remove_safe_env(
    ctx: typer.Context, names: list[str] | None = typer.Argument(None, metavar="NAME")
) -> None:
    """Remove environment variables from allow/deny lists."""
    allow, deny = _read_safe_env(ctx)
    items = list(names or [])
    if not items:
        name = prompt_if_missing(ctx, None, "Environment variable name")
        if name is None:
            raise typer.BadParameter("NAME required")
        items = [name]
    for name in items:
        allow.discard(name.lstrip("+-"))
        deny.discard(name.lstrip("+-"))
    _write_safe_env(ctx, allow, deny)


def _parse_value(value: str) -> bool | str:
    low = value.lower()
    if low in TRUE_SET:
        return True
    if low in FALSE_SET:
        return False
    return value


def _set_pairs(ctx: typer.Context, pairs: list[str], use_global: bool) -> None:
    """Persist ``VAR=VALUE`` pairs to config sources."""
    force_global = use_global or any(p.split("=", 1)[0] == "interactive" for p in pairs)
    if force_global:
        cfg = dict(ctx.obj.get("global_config", {}))
        for item in pairs:
            try:
                key, value = item.split("=", 1)
            except ValueError as exc:  # pragma: no cover - handled by typer
                raise typer.BadParameter("Use VAR=VALUE syntax") from exc
            key = key.strip().upper()
            if key not in KNOWN_KEYS:
                raise typer.BadParameter(f"Unknown config key '{key}'")
            parsed = _parse_value(value)
            env_val = (
                "true"
                if parsed is True
                else "false" if parsed is False else str(parsed)
            )
            os.environ[key] = env_val
            cfg[key] = parsed
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
            key = key.strip().upper()
            if key not in KNOWN_KEYS:
                raise typer.BadParameter(f"Unknown config key '{key}'")
            parsed = _parse_value(value)
            env_val = (
                "true"
                if parsed is True
                else "false" if parsed is False else str(parsed)
            )
            os.environ[key] = env_val
            set_key(str(env_path), key, env_val, quote_mode="never")
            env_path.chmod(0o600)
    global_cfg, _env_vals, merged = read_configs()
    ctx.obj.update({"global_config": global_cfg, "config": merged})
    refresh_completer()


@app.callback()
def config(
    ctx: typer.Context,
    pairs: list[str] = typer.Option(None, "--set", metavar="VAR=VALUE"),
    global_scope: bool = typer.Option(
        False, "--global", help="Modify global config instead of project .env"
    ),
) -> None:
    """Configuration command group.

    Examples:
        doc-ai config show
    """
    if ctx.obj is None:
        ctx.obj = {}
    if pairs:
        _set_pairs(ctx, pairs, global_scope)
        raise typer.Exit()


def _print_settings(ctx: typer.Context) -> None:
    logger.info("Current settings:")
    verbose, level, log_file = get_logging_options(ctx)
    logger.info("  verbose: %s", verbose)
    if level is not None:
        logger.info("  log_level: %s", level)
    if log_file is not None:
        logger.info("  log_file: %s", log_file)
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
                str(os.getenv(var, "") or "-"),
                str(env_cfg.get(var, "-") or "-"),
                str(global_cfg.get(var, "-") or "-"),
                str(defaults.get(var, "-") or "-"),
            )
        console.print(table)


@app.command()
def show(ctx: typer.Context) -> None:
    """Display current settings."""
    _print_settings(ctx)


@app.command("set")
def set_value(
    ctx: typer.Context,
    pairs: list[str] | None = typer.Argument(None, metavar="VAR=VALUE"),
    global_scope: bool = typer.Option(
        False, "--global", help="Modify global config instead of project .env"
    ),
) -> None:
    """Update environment configuration."""
    items = list(pairs or [])
    if not items:
        pair = prompt_if_missing(ctx, None, "VAR=VALUE")
        if pair is None:
            raise typer.BadParameter("VAR=VALUE required")
        items = [pair]
    _set_pairs(ctx, items, global_scope)


@app.command()
def toggle(
    ctx: typer.Context,
    key: str | None = typer.Argument(None, metavar="KEY"),
    global_scope: bool = typer.Option(
        False,
        "--global",
        help="Modify global config instead of project .env",
    ),
) -> None:
    """Toggle a boolean configuration value."""
    key = prompt_if_missing(ctx, key, "KEY")
    if key is None:
        raise typer.BadParameter("KEY required")
    key = key.strip().upper()
    if key not in BOOLEAN_KEYS:
        raise typer.BadParameter(f"Unknown boolean config key '{key}'")
    current = os.getenv(key, "")
    new_val = "false" if current.lower() in TRUE_SET else "true"
    _set_pairs(ctx, [f"{key}={new_val}"], global_scope)


@app.command("default-doc-type")
def default_doc_type(
    ctx: typer.Context,
    doc_type: str | None = typer.Argument(None, help="Default document type"),
) -> None:
    """Set or clear the default document type."""
    cfg = dict(ctx.obj.get("global_config", {}))
    if doc_type:
        cfg["default_doc_type"] = doc_type
        typer.echo(f"Default document type set to '{doc_type}'")
    else:
        cfg.pop("default_doc_type", None)
        typer.echo("Default document type cleared")
    save_global_config(cfg)
    global_cfg, _env_vals, merged = read_configs()
    ctx.obj.update({"global_config": global_cfg, "config": merged})
    refresh_completer()


@app.command("default-topic")
def default_topic(
    ctx: typer.Context,
    topic: str | None = typer.Argument(None, help="Default analysis topic"),
) -> None:
    """Set or clear the default analysis topic."""
    cfg = dict(ctx.obj.get("global_config", {}))
    if topic:
        cfg["default_topic"] = topic
        typer.echo(f"Default topic set to '{topic}'")
    else:
        cfg.pop("default_topic", None)
        typer.echo("Default topic cleared")
    save_global_config(cfg)
    global_cfg, _env_vals, merged = read_configs()
    ctx.obj.update({"global_config": global_cfg, "config": merged})
    refresh_completer()


def set_defaults(
    ctx: typer.Context,
    pairs: list[str] | None = typer.Argument(None, metavar="VAR=VALUE"),
) -> None:
    """Update runtime default options for the current session."""
    items = list(pairs or [])
    if not items:
        pair = prompt_if_missing(ctx, None, "VAR=VALUE")
        if pair is None:
            raise typer.BadParameter("VAR=VALUE required")
        items = [pair]
    root = ctx.find_root()
    if root.default_map is None:
        root.default_map = {}
    for item in items:
        try:
            key, value = item.split("=", 1)
        except ValueError as exc:  # pragma: no cover - handled by typer
            raise typer.BadParameter("Use VAR=VALUE syntax") from exc
        root.default_map[key] = value
    table = Table("Option", "Value")
    for key, value in sorted(root.default_map.items()):
        table.add_row(key, str(value))
    console.print(Panel(table, title="Runtime defaults"))


@app.command()
def wizard(
    ctx: typer.Context,
    global_scope: bool = typer.Option(
        False, "--global", help="Modify global config instead of project .env"
    ),
) -> None:
    """Run an interactive configuration wizard."""

    if ctx.obj is None:
        ctx.obj = {}
    try:
        interactive = bool(ctx.obj.get("interactive", True)) and sys.stdin.isatty()
    except Exception:
        interactive = False
    if not interactive:
        typer.echo("Interactive prompts disabled; no changes made")
        return
    defaults = load_env_defaults()
    pairs: list[str] = []
    for key, default in defaults.items():
        try:
            answer = questionary.text(key, default=str(default or "")).ask()
        except Exception:  # pragma: no cover - best effort
            answer = default or ""
        if answer:
            pairs.append(f"{key}={answer}")
    if pairs:
        _set_pairs(ctx, pairs, global_scope)
