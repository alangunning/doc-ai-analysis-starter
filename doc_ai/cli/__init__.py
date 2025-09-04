"""CLI orchestrator for AI document analysis pipeline."""
from __future__ import annotations

import logging
import os
import sys
import traceback
import importlib
from pathlib import Path
from typing import Optional

import typer
from dotenv import find_dotenv, load_dotenv
from rich.console import Console
from typer.completion import Shells, completion_init, get_completion_script

from doc_ai import __version__
from doc_ai.converter import OutputFormat, convert_path
from .interactive import get_completions, interactive_shell
from .utils import (
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
    add_completion=False,
)

SETTINGS = {"verbose": os.getenv("VERBOSE", "").lower() in {"1", "true", "yes"}}
DEFAULT_LOG_LEVEL = "DEBUG" if SETTINGS["verbose"] else "WARNING"

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

# Supported model names for CLI options.
SUPPORTED_MODELS = {
    "gpt-4.1",
    "gpt-4o",
    "gpt-4o-mini",
    "o3-mini",
}


def _validate_model(value: str | None) -> str | None:
    if value is None:
        return value
    if value not in SUPPORTED_MODELS:
        valid = ", ".join(sorted(SUPPORTED_MODELS))
        raise typer.BadParameter(
            f"Unknown model '{value}'. Choose from: {valid}"
        )
    return value


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
    logging.basicConfig(level=level)
    SETTINGS["verbose"] = level <= logging.DEBUG
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


@app.command()
def completion(shell: Shells):
    """Generate shell completion script."""
    completion_init()
    prog_name = "doc-ai"
    complete_var = f"_{prog_name.replace('-', '_').upper()}_COMPLETE"
    script = get_completion_script(
        prog_name=prog_name, complete_var=complete_var, shell=shell.value
    )
    typer.echo(script)


# Register subcommands implemented in dedicated modules.
from . import analyze as analyze_cmd
from . import config as config_cmd
from . import convert as convert_cmd
from . import embed as embed_cmd
pipeline_cmd = importlib.import_module("doc_ai.cli.pipeline")
from . import validate as validate_cmd

app.add_typer(config_cmd.app, name="config")
app.add_typer(convert_cmd.app, name="convert")
app.add_typer(validate_cmd.app, name="validate")
app.add_typer(analyze_cmd.app, name="analyze")
app.add_typer(embed_cmd.app, name="embed")
app.add_typer(pipeline_cmd.app, name="pipeline")

# Re-export pipeline callback for tests and external use.
from .pipeline import pipeline

__all__ = [
    "app",
    "analyze_doc",
    "validate_doc",
    "convert_path",
    "validate_file",
    "run_prompt",
    "interactive_shell",
    "get_completions",
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
            if SETTINGS["verbose"]:
                traceback.print_exc()
            else:
                console.print(f"[red]{exc}[/red]")
        return
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        app(prog_name="cli.py", args=["--help"])
        return
    console.print(
        "Starting interactive Doc AI shell. Type 'exit' or 'quit' to leave."
    )
    interactive_shell(
        app,
        console=console,
        print_banner=_print_banner,
        verbose=SETTINGS["verbose"],
    )
    console.print("Goodbye!")
