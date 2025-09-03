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

# Ensure project root is first on sys.path when running as a script.
if __package__ in (None, ""):
    sys.path[0] = str(Path(__file__).resolve().parent.parent)

from doc_ai.converter import OutputFormat, convert_path
from doc_ai.github import build_vector_store, validate_file, run_prompt
from .utils import (
    analyze_doc,
    infer_format as _infer_format,
    load_env_defaults,
    parse_env_formats as _parse_env_formats,
    suffix as _suffix,
    validate_doc,
)

ENV_FILE = find_dotenv(usecwd=True, raise_error_if_not_found=False) or ".env"
load_dotenv(ENV_FILE)

console = Console()
app = typer.Typer(
    help="Orchestrate conversion, validation, analysis and embedding generation.",
    add_completion=False,
)

SETTINGS = {"verbose": os.getenv("VERBOSE", "").lower() in {"1", "true", "yes"}}


@app.callback()
def _main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Global options."""
    SETTINGS["verbose"] = verbose


ASCII_ART = r"""
 ____   ___   ____      _      ___
|  _ \ / _ \ / ___|    / \    |_ _|
| | | | | | | |       / _ \    | |
| |_| | |_| | |___   / ___ \   | |
|____/ \___/ \____| /_/   \_\ |___|
"""


def _print_banner() -> None:  # pragma: no cover - visual flair only
    console.print(f"[bold green]{ASCII_ART}[/bold green]")


@app.command()
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
        for item in set_vars:
            try:
                key, value = item.split("=", 1)
            except ValueError as exc:  # pragma: no cover - handled by typer
                raise typer.BadParameter("Use VAR=VALUE syntax") from exc
            os.environ[key] = value
            set_key(str(env_path), key, value, quote_mode="never")
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
    source: str = typer.Argument(
        ..., help="Path or URL to raw document or folder"
    ),
    format: list[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s). Can be passed multiple times.",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Select files via checkbox prompt when SOURCE is a directory",
    ),
) -> None:
    """Convert files using Docling."""
    fmts = format or _parse_env_formats() or [OutputFormat.MARKDOWN]
    if not SETTINGS["verbose"]:
        warnings.filterwarnings("ignore")
    if source.startswith(("http://", "https://")):
        results = convert_path(source, fmts)
    else:
        path = Path(source)
        if interactive and path.is_dir():
            try:
                import questionary
            except Exception as exc:  # pragma: no cover - import guard
                raise typer.BadParameter(
                    "questionary is required for interactive mode"
                ) from exc
            files = [str(p) for p in path.iterdir() if p.is_file()]
            if not files:
                console.print("No files found.")
                return
            selected = questionary.checkbox(
                "Select files to convert", choices=files
            ).ask()
            if not selected:
                console.print("No files selected.")
                return
            results: list[Path] = []
            for sel in selected:
                results.extend(convert_path(Path(sel), fmts))
        else:
            results = convert_path(path, fmts)
    if not results:
        console.print("No new files to process.")


@app.command()
def validate(
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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Write request/response details to this file"
    ),
) -> None:
    """Validate converted output against the original file."""
    logger: logging.Logger | None = None
    log_path = log_file
    console_local = Console()
    if verbose or log_path is not None:
        logger = logging.getLogger("doc_ai.validate")
        logger.setLevel(logging.DEBUG)
        if verbose:
            from rich.logging import RichHandler

            sh = RichHandler(console=console_local, show_time=False)
            sh.setLevel(logging.DEBUG)
            logger.addHandler(sh)
        if log_path is None:
            log_path = raw.with_suffix(".validate.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)

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
) -> None:
    """Run an analysis prompt against a converted document."""
    markdown_doc = source
    if ".converted" not in "".join(markdown_doc.suffixes):
        used_fmt = fmt or OutputFormat.MARKDOWN
        markdown_doc = source.with_name(source.name + _suffix(used_fmt))
    analyze_doc(markdown_doc, prompt, output, model, base_model_url)


@app.command()
def embed(
    source: Path = typer.Argument(..., help="Directory containing Markdown files"),
) -> None:
    """Generate embeddings for Markdown files."""
    build_vector_store(source)


@app.command("pipeline")
def pipeline(
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
) -> None:
    """Run the full pipeline: convert, validate, analyze, and embed."""
    fmts = format or _parse_env_formats() or [OutputFormat.MARKDOWN]
    convert_path(source, fmts)
    validation_prompt = Path(
        ".github/prompts/validate-output.validate.prompt.yaml"
    )
    for raw_file in source.rglob("*"):
        if not raw_file.is_file():
            continue
        md_file = raw_file.with_name(raw_file.name + _suffix(OutputFormat.MARKDOWN))
        if md_file.exists():
            validate_doc(
                raw_file,
                md_file,
                OutputFormat.MARKDOWN,
                validation_prompt,
                model,
                base_model_url,
            )
            analyze_doc(md_file, prompt=prompt, model=model, base_url=base_model_url)
    build_vector_store(source)


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
    if len(sys.argv) > 1:
        _print_banner()
        args = sys.argv[1:]
        if SETTINGS["verbose"] and "--verbose" not in args and "-v" not in args:
            args.append("--verbose")
        try:
            app(prog_name="cli.py", args=args)
        except Exception as exc:  # pragma: no cover - runtime error display
            if SETTINGS["verbose"]:
                traceback.print_exc()
            else:
                console.print(f"[red]{exc}[/red]")
    else:
        interactive_shell(
            app,
            console=console,
            print_banner=_print_banner,
            verbose=SETTINGS["verbose"],
        )
