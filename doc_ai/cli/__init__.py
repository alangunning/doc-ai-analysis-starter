"""CLI orchestrator for AI document analysis pipeline."""
from __future__ import annotations

import logging
import os
import sys
import importlib
from enum import Enum
from pathlib import Path

import typer
from dotenv import find_dotenv, load_dotenv
from rich.console import Console

from doc_ai import __version__
from doc_ai.converter import OutputFormat, convert_path  # noqa: F401
from .interactive import interactive_shell  # noqa: F401
from .utils import (  # noqa: F401
    EXTENSION_MAP,
    analyze_doc,
    infer_format as _infer_format,
    load_env_defaults,
    parse_env_formats as _parse_env_formats,
    suffix as _suffix,
    validate_doc,
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

SETTINGS = {
    "verbose": os.getenv("VERBOSE", "").lower() in {"1", "true", "yes"},
    "banner": os.getenv("DOC_AI_BANNER", "").lower() in {"1", "true", "yes"},
}
DEFAULT_LOG_LEVEL = "DEBUG" if SETTINGS["verbose"] else "WARNING"

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
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Shortcut for --log-level DEBUG"
    ),
    log_level: str | None = typer.Option(
        None, "--log-level", help="Logging level (e.g. INFO, DEBUG)"
    ),
    banner: bool = typer.Option(
        False, "--banner/--quiet", help="Display ASCII banner before command"
    ),
) -> None:
    """Global options."""
    if version:
        console.print(__version__)
        raise typer.Exit()
    level_name = log_level
    if verbose:
        level_name = "DEBUG"
    if level_name is None:
        level_name = DEFAULT_LOG_LEVEL
    level = getattr(logging, level_name.upper(), logging.WARNING)
    logging.basicConfig(level=level, force=True)
    logging.captureWarnings(True)
    pywarn = logging.getLogger("py.warnings")
    if level <= logging.DEBUG:
        pywarn.setLevel(logging.WARNING)
    else:
        pywarn.setLevel(logging.ERROR)
    SETTINGS["verbose"] = level <= logging.DEBUG
    SETTINGS["banner"] = banner
    if banner:
        _print_banner()


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
def _exit_command() -> None:
    """Exit the interactive shell."""
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
pipeline_cmd = importlib.import_module("doc_ai.cli.pipeline")  # noqa: E402
from . import validate as validate_cmd  # noqa: E402

app.add_typer(config_cmd.app, name="config")
app.add_typer(convert_cmd.app, name="convert")
app.add_typer(validate_cmd.app, name="validate")
app.add_typer(analyze_cmd.app, name="analyze")
app.add_typer(embed_cmd.app, name="embed")
app.add_typer(pipeline_cmd.app, name="pipeline")

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
]


def main() -> None:
    """Entry point for running the CLI as a script."""
    load_dotenv(ENV_FILE)
    args = sys.argv[1:]
    if args:
        try:
            app(prog_name="cli.py", args=args)
        except Exception as exc:  # pragma: no cover - runtime error display
            if logger.isEnabledFor(logging.DEBUG):
                logger.exception("Unhandled exception")
            else:
                logger.error("%s", exc)
                console.print(f"[red]{exc}[/red]")
        return
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        app(prog_name="cli.py", args=["--help"])
        return
    if SETTINGS["banner"]:
        _print_banner()
        try:
            app(prog_name="cli.py", args=["--help"])
        except SystemExit:
            pass
    console.print("Starting interactive Doc AI shell. Type 'exit' or 'quit' to leave.")
    interactive_shell(app)
    console.print("Goodbye!")
