# mypy: ignore-errors
"""CLI orchestrator for AI document analysis pipeline."""

from __future__ import annotations

import json
import logging
import os
import sys
import importlib
import hashlib
import hmac
from importlib.metadata import entry_points
from enum import Enum
from pathlib import Path

import click
import typer
from dotenv import find_dotenv, load_dotenv, dotenv_values
from platformdirs import PlatformDirs
from rich.console import Console
import yaml
from typer.main import get_command

from doc_ai import __version__
from doc_ai.converter import OutputFormat, convert_path  # noqa: F401
from doc_ai.logging import configure_logging
from .interactive import (
    interactive_shell,
    run_batch,
    discover_doc_types_topics,
)  # noqa: F401
import doc_ai.cli.interactive as interactive_module
from .utils import (  # noqa: F401
    EXTENSION_MAP,
    analyze_doc,
    infer_format as _infer_format,
    parse_env_formats as _parse_env_formats,
    suffix as _suffix,
    validate_doc,
    prompt_if_missing,
)

# Ensure project root is first on sys.path when running as a script.
if __package__ in (None, ""):
    sys.path[0] = str(Path(__file__).resolve().parent.parent)

ENV_FILE = find_dotenv(usecwd=True, raise_error_if_not_found=False) or ".env"

console = Console()
app = typer.Typer(
    help="Orchestrate conversion, validation, analysis and embedding generation.",
    add_completion=True,
)

dirs = PlatformDirs("doc_ai")
GLOBAL_CONFIG_DIR = Path(dirs.user_config_dir)
for ext in (".json", ".yaml", ".yml"):
    candidate = GLOBAL_CONFIG_DIR / f"config{ext}"
    if candidate.exists():
        GLOBAL_CONFIG_PATH = candidate
        break
else:
    GLOBAL_CONFIG_PATH = GLOBAL_CONFIG_DIR / "config.json"


def load_global_config() -> dict[str, str]:
    if GLOBAL_CONFIG_PATH.exists():
        try:
            if GLOBAL_CONFIG_PATH.suffix in {".yaml", ".yml"}:
                return yaml.safe_load(GLOBAL_CONFIG_PATH.read_text()) or {}
            return json.loads(GLOBAL_CONFIG_PATH.read_text())
        except Exception as exc:
            logger.warning(
                "Failed to load global config from %s: %s",
                GLOBAL_CONFIG_PATH,
                exc,
            )
            return {}
    return {}


def save_global_config(cfg: dict[str, str]) -> None:
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if GLOBAL_CONFIG_PATH.suffix in {".yaml", ".yml"}:
        GLOBAL_CONFIG_PATH.write_text(yaml.safe_dump(cfg))
    else:
        GLOBAL_CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def read_configs() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    global_cfg = load_global_config()
    env_vals: dict[str, str] = {}
    if Path(ENV_FILE).exists():
        env_vals = dotenv_values(ENV_FILE)  # type: ignore[assignment]
    merged = {**global_cfg, **env_vals, **os.environ}
    return global_cfg, env_vals, merged


logger = logging.getLogger(__name__)

# File extensions considered raw inputs for the pipeline.
RAW_SUFFIXES = {
    ".pdf",
    ".docx",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
    ".svg",
}


class ModelName(str, Enum):
    """Supported model names for CLI options."""

    GPT_4_1 = "gpt-4.1"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    O3_MINI = "o3-mini"


def _validate_prompt(value: Path | None) -> Path | None:
    if value is not None and not value.exists():
        raise typer.BadParameter(f"Prompt file not found: {value}")
    return value


@app.callback()
def _main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit"
    ),
    verbose: bool | None = typer.Option(
        None, "--verbose", "-v", help="Shortcut for --log-level DEBUG"
    ),
    log_level: str | None = typer.Option(
        None, "--log-level", help="Logging level (e.g. INFO, DEBUG)"
    ),
    log_file: Path | None = typer.Option(
        None, "--log-file", help="Write logs to the given file"
    ),
    banner: bool | None = typer.Option(
        None, "--banner/--quiet", help="Display ASCII banner before command"
    ),
    interactive: bool | None = typer.Option(
        None,
        "--interactive/--no-interactive",
        help="Start interactive shell when no command is provided",
    ),
) -> None:
    """Global options."""
    if version:
        typer.echo(__version__)
        raise typer.Exit()

    global_cfg, _env_vals, merged = read_configs()
    ctx.obj = {
        "config": merged,
        "global_config": global_cfg,
    }

    verbose_default = merged.get("VERBOSE", "").lower() in {"1", "true", "yes"}
    banner_default = merged.get("DOC_AI_BANNER", "").lower() in {"1", "true", "yes"}
    interactive_default = merged.get("interactive", "true").lower() in {
        "1",
        "true",
        "yes",
    }

    effective_verbose = verbose if verbose is not None else verbose_default
    level_name = log_level if log_level is not None else merged.get("LOG_LEVEL")
    if effective_verbose:
        level_name = "DEBUG"
    if level_name is None:
        level_name = "DEBUG" if verbose_default else "WARNING"
    if isinstance(level_name, str):
        numeric_level = logging.getLevelName(level_name.upper())
        if isinstance(numeric_level, str):
            allowed = ", ".join(
                ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
            )
            raise typer.BadParameter(
                f"Invalid log level '{level_name}'. Allowed levels: {allowed}"
            )
        level_name = level_name.upper()
    log_file_val = log_file if log_file is not None else merged.get("LOG_FILE")
    log_file_path = (
        Path(log_file_val)
        if isinstance(log_file_val, (str, Path)) and log_file_val
        else None
    )
    configure_logging(level_name, log_file_path)
    ctx.obj["log_level"] = level_name
    ctx.obj["log_file"] = log_file_path
    ctx.obj["verbose"] = logging.getLogger().level <= logging.DEBUG
    banner_flag = banner if banner is not None else banner_default
    ctx.obj["banner"] = banner_flag
    if banner_flag:
        _print_banner()
    interactive_flag = interactive if interactive is not None else interactive_default
    ctx.obj["interactive"] = interactive_flag


ASCII_ART = r"""
 ____   ___   ____      _      ___
|  _ \ / _ \ / ___|    / \    |_ _|
| | | | | | | |       / _ \    | |
| |_| | |_| | |___   / ___ \   | |
|____/ \___/ \____| /_/   \_\ |___|
"""


def _print_banner() -> None:  # pragma: no cover - visual flair only
    console.print(f"[bold green]{ASCII_ART}[/bold green]")


@app.command("exit")
@app.command("quit")
def _exit_command(ctx: typer.Context) -> None:
    """Exit the interactive shell."""
    raise typer.Exit()


@app.command()
def cd(ctx: typer.Context, path: Path | None = typer.Argument(None)) -> None:
    """Change the current working directory."""
    path_val = prompt_if_missing(ctx, str(path) if path is not None else None, "Path")
    if path_val is None:
        raise typer.BadParameter("Missing argument 'path'")
    path = Path(path_val)
    try:
        os.chdir(path)
    except OSError as exc:  # pragma: no cover - just error display
        logger.error("[red]%s[/red]", exc)
        raise typer.Exit(code=1)

    # Recompute .env location and refresh environment variables
    global ENV_FILE
    ENV_FILE = find_dotenv(usecwd=True, raise_error_if_not_found=False) or ".env"
    load_dotenv(ENV_FILE, override=True)

    # Reload configuration so subsequent commands see updated values
    global_cfg, _env_vals, merged = read_configs()
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["global_config"] = global_cfg
    ctx.obj["config"] = merged

    # Update prompt for interactive sessions
    if interactive_module.PROMPT_KWARGS is not None:
        interactive_module.PROMPT_KWARGS["message"] = (
            lambda: f"{interactive_module._prompt_name()}>"
        )
        comp = interactive_module.PROMPT_KWARGS.get("completer")
        if comp is not None and hasattr(comp, "refresh"):
            comp.refresh()

    # Ensure config submodule uses the new ENV_FILE if already imported
    try:  # pragma: no cover - defensive
        from . import config as config_module

        config_module.ENV_FILE = ENV_FILE
    except Exception:
        pass


@app.command("version")
def _version_command() -> None:
    """Show the installed ``doc-ai`` version."""
    typer.echo(__version__)
    raise typer.Exit()


def validate_file(*args, **kwargs):
    from doc_ai.github.validator import validate_file as _validate_file

    return _validate_file(*args, **kwargs)


def build_vector_store(*args, **kwargs):
    from doc_ai.github.vector import build_vector_store as _build_vector_store

    return _build_vector_store(*args, **kwargs)


def run_prompt(*args, **kwargs):
    from doc_ai.github.prompts import run_prompt as _run_prompt

    return _run_prompt(*args, **kwargs)


# Register subcommands implemented in dedicated modules.
from . import analyze as analyze_cmd  # noqa: E402
from . import config as config_cmd  # noqa: E402
from . import convert as convert_cmd  # noqa: E402
from . import embed as embed_cmd  # noqa: E402
from . import add as add_cmd  # noqa: E402
from . import manage_urls as manage_urls_cmd  # noqa: E402

pipeline_cmd = importlib.import_module("doc_ai.cli.pipeline")  # noqa: E402
from . import validate as validate_cmd  # noqa: E402
from . import query as query_cmd  # noqa: E402
from . import init_workflows as init_workflows_cmd  # noqa: E402
from . import new_doc_type as new_doc_type_cmd  # noqa: E402
from . import new_topic as new_topic_cmd  # noqa: E402
from . import prompt as prompt_cmd  # noqa: E402

app.add_typer(config_cmd.app, name="config")
app.add_typer(convert_cmd.app, name="convert")
app.add_typer(validate_cmd.app, name="validate")
app.add_typer(analyze_cmd.app, name="analyze")
app.add_typer(embed_cmd.app, name="embed")
app.add_typer(pipeline_cmd.app, name="pipeline")
app.add_typer(query_cmd.app, name="query")
app.add_typer(init_workflows_cmd.app, name="init-workflows")

new_app = typer.Typer(help="Scaffold new document types and topic prompts")
new_app.command("doc-type")(new_doc_type_cmd.doc_type)
new_app.command("topic")(new_topic_cmd.topic)
new_app.command("rename-doc-type")(new_doc_type_cmd.rename_doc_type)
new_app.command("delete-doc-type")(new_doc_type_cmd.delete_doc_type)
new_app.command("rename-topic")(new_topic_cmd.rename_topic)
new_app.command("delete-topic")(new_topic_cmd.delete_topic)
app.add_typer(new_app, name="new")

app.add_typer(add_cmd.app, name="add")
app.add_typer(manage_urls_cmd.app, name="urls")
app.command("set")(config_cmd.set_defaults)

# Prompt inspection and editing
show_app = typer.Typer(help="Display resources")
edit_app = typer.Typer(help="Modify resources")


@show_app.command("doc-types")
def show_doc_types() -> None:
    """List available document types discovered under the ``data`` directory."""

    doc_types, _ = discover_doc_types_topics()
    for name in doc_types:
        typer.echo(name)


@show_app.command("topics")
def show_topics() -> None:
    """List available analysis topics discovered from prompt files."""

    _, topics = discover_doc_types_topics()
    for name in topics:
        typer.echo(name)


@show_app.command("prompt")
def show_prompt(
    doc_type: str, topic: str | None = typer.Option(None, "--topic")
) -> None:
    """Print the contents of a prompt file for the given document type."""
    typer.echo(prompt_cmd.show_prompt(doc_type, topic))


@edit_app.command("prompt")
def edit_prompt(
    doc_type: str, topic: str | None = typer.Option(None, "--topic")
) -> None:
    """Open the prompt file in ``$EDITOR`` (falls back to ``vi``/``nano``)."""
    prompt_cmd.edit_prompt(doc_type, topic)


app.add_typer(show_app, name="show")
app.add_typer(edit_app, name="edit")


_LOADED_PLUGINS: dict[str, typer.Typer] = {}


def _hash_distribution(dist: object) -> str:
    """Return a SHA256 digest of a distribution's files."""
    root = Path(getattr(dist, "locate_file", lambda x: "")("") or "")
    digest = hashlib.sha256()
    if root and root.exists():
        for path in sorted(root.rglob("*")):
            if path.is_file():
                digest.update(path.read_bytes())
    return digest.hexdigest()


def _register_plugins() -> None:
    """Load Typer apps from ``doc_ai.plugins`` entry points."""
    _, _, merged = read_configs()
    raw = merged.get("DOC_AI_TRUSTED_PLUGINS", "")
    allowed: dict[str, str | None] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "==" in item:
            name, ver = item.split("==", 1)
            allowed[name.strip()] = ver.strip()
        else:
            allowed[item] = None

    hashes_raw = merged.get("DOC_AI_TRUSTED_PLUGIN_HASHES", "")
    expected_hashes: dict[str, str] = {}
    for item in hashes_raw.split(","):
        item = item.strip()
        if not item or "=" not in item:
            continue
        name, digest = item.split("=", 1)
        expected_hashes[name.strip()] = digest.strip()

    for ep in entry_points(group="doc_ai.plugins"):
        if ep.name in _LOADED_PLUGINS:
            continue

        dist = getattr(ep, "dist", None)
        pkg_name = getattr(dist, "metadata", {}).get("Name", "unknown")
        version = getattr(dist, "version", "unknown")
        logger.info("Discovered plugin %s from %s %s", ep.name, pkg_name, version)

        if ep.name not in allowed:
            logger.info("Skipping untrusted plugin %s", ep.name)
            continue
        expected_version = allowed[ep.name]
        if expected_version and expected_version != version:
            logger.error(
                "Skipping plugin %s: version %s does not match trusted %s",
                ep.name,
                version,
                expected_version,
            )
            continue

        expected_hash = expected_hashes.get(ep.name)
        if expected_hash and dist is not None:
            try:
                actual_hash = _hash_distribution(dist)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to hash plugin %s: %s", ep.name, exc)
                continue
            if not hmac.compare_digest(actual_hash, expected_hash):
                logger.error("Hash mismatch for plugin %s", ep.name)
                continue

        try:
            plugin_app = ep.load()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to load plugin %s: %s", ep.name, exc)
            continue
        if isinstance(plugin_app, typer.Typer):
            app.add_typer(plugin_app, name=ep.name)
            _LOADED_PLUGINS[ep.name] = plugin_app
        else:  # pragma: no cover - plugin contract
            logger.error("Plugin %s did not return a Typer app", ep.name)


plugins_app = typer.Typer(help="Utilities for inspecting plugins.")


@plugins_app.command("list")
def list_plugins() -> None:
    """Print the names of loaded plugins."""
    if not _LOADED_PLUGINS:
        typer.echo("No plugins loaded.")
        raise typer.Exit()
    for name in sorted(_LOADED_PLUGINS):
        typer.echo(name)


@plugins_app.command("trust")
def trust_plugin(name: str) -> None:
    """Add *name* to the plugin allowlist and attempt to load it."""
    cfg = load_global_config()
    raw = cfg.get("DOC_AI_TRUSTED_PLUGINS", "")
    allowed = {p.strip() for p in raw.split(",") if p.strip()}
    if name in allowed:
        typer.echo(f"Plugin '{name}' already trusted")
    else:
        allowed.add(name)
        cfg["DOC_AI_TRUSTED_PLUGINS"] = ",".join(sorted(allowed))
        save_global_config(cfg)
        typer.echo(f"Trusted plugin '{name}'")
    _register_plugins()


app.add_typer(plugins_app, name="plugins")


_register_plugins()

# Re-export pipeline callback for tests and external use.
from .pipeline import pipeline  # noqa: E402

__all__ = [
    "app",
    "analyze_doc",
    "validate_doc",
    "convert_path",
    "validate_file",
    "run_prompt",
    "interactive_shell",
    "main",
    "pipeline",
    "save_global_config",
    "read_configs",
]


def main() -> None:
    """Entry point for running the CLI as a script."""
    load_dotenv(ENV_FILE)
    args = sys.argv[1:]
    run_path: Path | None = None
    for i, arg in enumerate(list(args)):
        if arg == "--run":
            if i + 1 >= len(args):
                logger.error("[red]--run requires a path[/red]")
                raise SystemExit(1)
            run_path = Path(args[i + 1])
            del args[i : i + 2]
            break
        if arg.startswith("--run="):
            run_path = Path(arg.split("=", 1)[1])
            del args[i]
            break
    init_path: Path | None = None
    for flag in ("--init", "--batch"):
        for i, arg in enumerate(list(args)):
            if arg == flag:
                if i + 1 >= len(args):
                    logger.error("[red]%s requires a path[/red]", flag)
                    raise SystemExit(1)
                init_path = Path(args[i + 1])
                del args[i : i + 2]
                break
            if arg.startswith(f"{flag}="):
                init_path = Path(arg.split("=", 1)[1])
                del args[i]
                break
        if init_path is not None:
            break
    for path in (run_path, init_path):
        if path is not None and not path.exists():
            logger.error("[red]Batch file not found: %s[/red]", path)
            raise SystemExit(1)
    if run_path is not None:
        cmd = get_command(app)
        ctx = click.Context(cmd)
        try:
            run_batch(ctx, run_path)
        except typer.Exit as exc:
            raise SystemExit(exc.exit_code)
        return
    if args:
        try:
            app(prog_name="cli.py", args=args)
        except Exception as exc:  # pragma: no cover - runtime error display
            if logger.isEnabledFor(logging.DEBUG):
                logger.exception("Unhandled exception")
            else:
                logger.error("[red]%s[/red]", exc)
        return
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        app(prog_name="cli.py", args=["--help"])
        return
    _, _, merged = read_configs()
    banner_cfg = merged.get("DOC_AI_BANNER", "").lower() in {"1", "true", "yes"}
    interactive_cfg = merged.get("interactive", "true").lower() in {"1", "true", "yes"}
    if not interactive_cfg:
        if banner_cfg:
            _print_banner()
        try:
            app(prog_name="cli.py", args=["--help"])
        except SystemExit:
            pass
        return
    if banner_cfg:
        _print_banner()
        try:
            app(prog_name="cli.py", args=["--help"])
        except SystemExit:
            pass
    logger.info("Starting interactive Doc AI shell. Type 'exit' or 'quit' to leave.")
    interactive_shell(app, init=init_path)
    logger.info("Goodbye!")
