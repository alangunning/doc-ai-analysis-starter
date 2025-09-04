"""CLI orchestrator for AI document analysis pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import os
import sys
import traceback
import warnings
import logging

import typer
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv, set_key, find_dotenv
from .interactive import interactive_shell, get_completions
from doc_ai.logging_utils import setup_logging

# Ensure project root is first on sys.path when running as a script.
if __package__ in (None, ""):
    sys.path[0] = str(Path(__file__).resolve().parent.parent)

from doc_ai.converter import OutputFormat, convert_path
from doc_ai.converter.path import SUPPORTED_SUFFIXES
from .utils import (
    EXTENSION_MAP,
    analyze_doc,
    infer_format as _infer_format,
    load_env_defaults,
    parse_env_formats as _parse_env_formats,
    suffix as _suffix,
    validate_doc,
)

from doc_ai import __version__

ENV_FILE = find_dotenv(usecwd=True, raise_error_if_not_found=False) or ".env"

console = Console()
app = typer.Typer(
    help="Orchestrate conversion, validation, analysis and embedding generation.",
    add_completion=False,
)

SETTINGS = {
    "verbose": os.getenv("VERBOSE", "").lower() in {"1", "true", "yes"},
    "log_level": "INFO",
    "log_file": None,
}

# File extensions considered raw inputs for the pipeline.
RAW_SUFFIXES = {s for s in SUPPORTED_SUFFIXES if s not in EXTENSION_MAP}


@app.callback()
def _main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    log_level: str = typer.Option(
        "INFO", "--log-level", help="Logging level (DEBUG, INFO, WARN, ERROR)", case_sensitive=False
    ),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Write logs to this file"
    ),
) -> None:
    """Global options."""
    if version:
        console.print(__version__)
        raise typer.Exit()
    if verbose:
        log_level = "DEBUG"
    SETTINGS["verbose"] = verbose or log_level.upper() == "DEBUG"
    SETTINGS["log_level"] = log_level.upper()
    SETTINGS["log_file"] = log_file
    ctx.obj = {"log_level": SETTINGS["log_level"], "log_file": log_file}
    setup_logging(log_level, log_file)


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
def config(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        None, "--verbose/--no-verbose", help="Toggle verbose error output"
    ),
    set_vars: list[str] = typer.Option(
        None,
        "--set",
        help="Set VAR=VALUE pairs to update environment configuration",
        metavar="VAR=VALUE",
    ),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Write logs to this file"
    ),
) -> None:
    """Show or update runtime configuration."""
    setup_logging(ctx.obj["log_level"], log_file or ctx.obj.get("log_file"))
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


@app.command()
def convert(
    ctx: typer.Context,
    source: str = typer.Argument(
        ..., help="Path or URL to raw document or folder"
    ),
    format: list[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s). Can be passed multiple times.",
    ),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Write logs to this file"
    ),
) -> None:
    """Convert files using Docling."""
    setup_logging(ctx.obj["log_level"], log_file or ctx.obj.get("log_file"))
    fmts = format or _parse_env_formats() or [OutputFormat.MARKDOWN]
    if not SETTINGS["verbose"]:
        warnings.filterwarnings("ignore")
    if source.startswith(("http://", "https://")):
        results = convert_path(source, fmts)
    else:
        results = convert_path(Path(source), fmts)
    if not results:
        console.print("No new files to process.")


@app.command()
def validate(
    ctx: typer.Context,
    raw: Path = typer.Argument(..., help="Path to raw document"),
    rendered: Path | None = typer.Argument(
        None, help="Path to converted file"
    ),
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f"),
    prompt: Optional[Path] = typer.Option(
        None,
        "--prompt",
        help="Prompt file (overrides auto-detected *.validate.prompt.yaml)",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model name override"
    ),
    base_model_url: Optional[str] = typer.Option(
        None, "--base-model-url", help="Model base URL override"
    ),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Write request/response details to this file"
    ),
) -> None:
    """Validate converted output against the original file."""
    setup_logging(ctx.obj["log_level"], log_file or ctx.obj.get("log_file"))
    logger = logging.getLogger("doc_ai.validate")
    console_local = Console()

    if rendered is None:
        used_fmt = fmt or OutputFormat.MARKDOWN
        rendered = raw.with_name(raw.name + _suffix(used_fmt))
    else:
        used_fmt = fmt or _infer_format(rendered)

    validate_doc(
        raw,
        rendered,
        used_fmt,
        prompt,
        model,
        base_model_url,
        show_progress=True,
        logger=logger,
        console=console_local,
    )


@app.command()
def analyze(
    ctx: typer.Context,
    source: Path = typer.Argument(..., help="Raw or converted document"),
    fmt: Optional[OutputFormat] = typer.Option(
        None, "--format", "-f", help="Format of converted file"
    ),
    prompt: Path | None = typer.Option(
        None,
        "--prompt",
        "-p",
        help="Prompt file (overrides auto-detected *.analysis.prompt.yaml)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Optional output file; defaults to <doc>.analysis.json",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model name override"
    ),
    base_model_url: Optional[str] = typer.Option(
        None, "--base-model-url", help="Model base URL override"
    ),
    require_json: bool = typer.Option(
        False,
        "--require-structured",
        help="Fail if analysis output is not valid JSON",
        is_flag=True,
    ),
    fail_fast: bool = typer.Option(
        True,
        "--fail-fast/--keep-going",
        help="Stop processing on first validation or analysis failure",
    ),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Write logs to this file"
    ),
) -> None:
    """Run an analysis prompt against a converted document."""
    setup_logging(ctx.obj["log_level"], log_file or ctx.obj.get("log_file"))
    markdown_doc = source
    if ".converted" not in "".join(markdown_doc.suffixes):
        used_fmt = fmt or OutputFormat.MARKDOWN
        markdown_doc = source.with_name(source.name + _suffix(used_fmt))
    analyze_doc(markdown_doc, prompt, output, model, base_model_url, require_json)


@app.command()
def embed(
    ctx: typer.Context,
    source: Path = typer.Argument(..., help="Directory containing Markdown files"),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Write logs to this file"
    ),
) -> None:
    """Generate embeddings for Markdown files."""
    setup_logging(ctx.obj["log_level"], log_file or ctx.obj.get("log_file"))
    build_vector_store(source)


@app.command("pipeline")
def pipeline(
    ctx: typer.Context,
    source: Path = typer.Argument(..., help="Directory with raw documents"),
    prompt: Path = typer.Option(
        Path(".github/prompts/doc-analysis.analysis.prompt.yaml"),
        help="Analysis prompt file",
    ),
    format: list[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s) for conversion",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model name override"
    ),
    base_model_url: Optional[str] = typer.Option(
        None, "--base-model-url", help="Model base URL override"
    ),
    fail_fast: bool = typer.Option(
        True,
        "--fail-fast/--keep-going",
        help="Stop processing on first validation or analysis failure",
    ),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Write logs to this file"
    ),
) -> None:
    """Run the full pipeline: convert, validate, analyze, and embed."""
    setup_logging(ctx.obj["log_level"], log_file or ctx.obj.get("log_file"))
    fmts = format or _parse_env_formats() or [OutputFormat.MARKDOWN]
    convert_path(source, fmts)
    validation_prompt = Path(
        ".github/prompts/validate-output.validate.prompt.yaml"
    )
    failures: list[tuple[str, Path, Exception]] = []
    for raw_file in source.rglob("*"):
        if (
            not raw_file.is_file()
            or raw_file.suffix.lower() not in RAW_SUFFIXES
            or any(".converted" in part for part in raw_file.parts)
        ):
            continue
        md_file = raw_file.with_name(raw_file.name + _suffix(OutputFormat.MARKDOWN))
        if md_file.exists():
            try:
                validate_doc(
                    raw_file,
                    md_file,
                    OutputFormat.MARKDOWN,
                    validation_prompt,
                    model,
                    base_model_url,
                )
            except Exception as exc:  # pragma: no cover - error handling
                failures.append(("validation", raw_file, exc))
                console.print(
                    f"[red]Validation failed for {raw_file}: {exc}[/red]"
                )
                if fail_fast:
                    break
            try:
                analyze_doc(
                    md_file, prompt=prompt, model=model, base_url=base_model_url
                )
            except Exception as exc:  # pragma: no cover - error handling
                failures.append(("analysis", md_file, exc))
                console.print(
                    f"[red]Analysis failed for {md_file}: {exc}[/red]"
                )
                if fail_fast:
                    break
    build_vector_store(source)
    if failures:
        console.print("[bold red]Failures encountered during pipeline:[/bold red]")
        for step, path, exc in failures:
            console.print(f"- {step} {path}: {exc}")
        raise typer.Exit(code=1)


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
]


def main() -> None:
    """Entry point for running the CLI as a script."""
    load_dotenv(ENV_FILE)
    if len(sys.argv) > 1:
        _print_banner()
        args = sys.argv[1:]
        if SETTINGS["verbose"] and "--log-level" not in args:
            args.extend(["--log-level", "DEBUG"])
        try:
            app(prog_name="cli.py", args=args)
        except Exception as exc:  # pragma: no cover - runtime error display
            if SETTINGS["verbose"]:
                traceback.print_exc()
            else:
                console.print(f"[red]{exc}[/red]")
    else:
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
