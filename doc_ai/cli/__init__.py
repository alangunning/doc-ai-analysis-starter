"""CLI orchestrator for AI document analysis pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import os
import sys
import shlex
import traceback
import warnings
import logging
import importlib.metadata

import typer
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

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

load_dotenv()

console = Console()
app = typer.Typer(
    help="Orchestrate conversion, validation, analysis and embedding generation.",
    add_completion=False,
)

CONFIG = {"verbose": os.getenv("VERBOSE", "").lower() in {"1", "true", "yes"}}


def _version_callback(value: bool) -> None:
    """Print package version and exit."""
    if value:
        try:
            version = importlib.metadata.version("doc-ai-starter")
        except importlib.metadata.PackageNotFoundError:
            version = "0.1.0"
        typer.echo(version)
        raise typer.Exit()


@app.callback()
def _main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show package version and exit",
    ),
) -> None:
    """Global options."""
    CONFIG["verbose"] = verbose


ASCII_ART = r"""
 ____   ___   ____      _    ___    ____ _     ___
|  _ \ / _ \ / ___|    / \  |_ _|  / ___| |   |_ _|
| | | | | | | |       / _ \  | |  | |   | |    | |
| |_| | |_| | |___   / ___ \ | |  | |___| |___ | |
|____/ \___/ \____| /_/   \_\___|  \____|_____|___|
"""


def _print_banner() -> None:  # pragma: no cover - visual flair only
    console.print(f"[bold green]{ASCII_ART}[/bold green]")


@app.command()
def config(
    verbose: bool = typer.Option(
        None, "--verbose/--no-verbose", help="Toggle verbose error output"
    ),
    docs_site_url: Optional[str] = typer.Option(None, "--docs-site-url", help="Base site URL for docs"),
    docs_base_url: Optional[str] = typer.Option(None, "--docs-base-url", help="Base path for docs"),
    github_org: Optional[str] = typer.Option(None, "--github-org", help="GitHub organisation"),
    github_repo: Optional[str] = typer.Option(None, "--github-repo", help="GitHub repository"),
    pr_review_model: Optional[str] = typer.Option(None, "--pr-review-model", help="Model for PR review"),
    validate_model: Optional[str] = typer.Option(None, "--validate-model", help="Model for validation"),
    analyze_model: Optional[str] = typer.Option(None, "--analyze-model", help="Model for analysis"),
    embed_model: Optional[str] = typer.Option(None, "--embed-model", help="Embedding model"),
    embed_dimensions: Optional[int] = typer.Option(None, "--embed-dimensions", help="Embedding dimensions override"),
    base_model_url: Optional[str] = typer.Option(None, "--base-model-url", help="Default model base URL"),
    openai_api_key: Optional[str] = typer.Option(None, "--openai-api-key", help="OpenAI API key"),
    validate_base_model_url: Optional[str] = typer.Option(None, "--validate-base-model-url", help="Base URL for validation"),
    output_formats: Optional[str] = typer.Option(None, "--output-formats", help="Default formats for convert"),
    disable_all_workflows: Optional[bool] = typer.Option(
        None,
        "--disable-all-workflows",
        "--enable-all-workflows",
        help="Disable all GitHub workflows",
    ),
    enable_convert_workflow: Optional[bool] = typer.Option(
        None,
        "--enable-convert-workflow",
        "--disable-convert-workflow",
        help="Toggle convert workflow",
    ),
    enable_validate_workflow: Optional[bool] = typer.Option(
        None,
        "--enable-validate-workflow",
        "--disable-validate-workflow",
        help="Toggle validate workflow",
    ),
    enable_vector_workflow: Optional[bool] = typer.Option(
        None,
        "--enable-vector-workflow",
        "--disable-vector-workflow",
        help="Toggle vector workflow",
    ),
    enable_prompt_analysis_workflow: Optional[bool] = typer.Option(
        None,
        "--enable-prompt-analysis-workflow",
        "--disable-prompt-analysis-workflow",
        help="Toggle prompt analysis workflow",
    ),
    enable_pr_review_workflow: Optional[bool] = typer.Option(
        None,
        "--enable-pr-review-workflow",
        "--disable-pr-review-workflow",
        help="Toggle PR review workflow",
    ),
    enable_docs_workflow: Optional[bool] = typer.Option(
        None,
        "--enable-docs-workflow",
        "--disable-docs-workflow",
        help="Toggle docs workflow",
    ),
    enable_lint_workflow: Optional[bool] = typer.Option(
        None,
        "--enable-lint-workflow",
        "--disable-lint-workflow",
        help="Toggle lint workflow",
    ),
    enable_auto_merge_workflow: Optional[bool] = typer.Option(
        None,
        "--enable-auto-merge-workflow",
        "--disable-auto-merge-workflow",
        help="Toggle auto merge workflow",
    ),
) -> None:
    """Show or update configuration defaults."""
    from dotenv import set_key

    if verbose is not None:
        CONFIG["verbose"] = verbose

    dotenv_path = Path(__file__).resolve().parents[2] / ".env"
    updates: dict[str, Optional[str | int | bool]] = {
        "DOCS_SITE_URL": docs_site_url,
        "DOCS_BASE_URL": docs_base_url,
        "GITHUB_ORG": github_org,
        "GITHUB_REPO": github_repo,
        "PR_REVIEW_MODEL": pr_review_model,
        "VALIDATE_MODEL": validate_model,
        "ANALYZE_MODEL": analyze_model,
        "EMBED_MODEL": embed_model,
        "EMBED_DIMENSIONS": embed_dimensions,
        "BASE_MODEL_URL": base_model_url,
        "OPENAI_API_KEY": openai_api_key,
        "VALIDATE_BASE_MODEL_URL": validate_base_model_url,
        "OUTPUT_FORMATS": output_formats,
        "DISABLE_ALL_WORKFLOWS": disable_all_workflows,
        "ENABLE_CONVERT_WORKFLOW": enable_convert_workflow,
        "ENABLE_VALIDATE_WORKFLOW": enable_validate_workflow,
        "ENABLE_VECTOR_WORKFLOW": enable_vector_workflow,
        "ENABLE_PROMPT_ANALYSIS_WORKFLOW": enable_prompt_analysis_workflow,
        "ENABLE_PR_REVIEW_WORKFLOW": enable_pr_review_workflow,
        "ENABLE_DOCS_WORKFLOW": enable_docs_workflow,
        "ENABLE_LINT_WORKFLOW": enable_lint_workflow,
        "ENABLE_AUTO_MERGE_WORKFLOW": enable_auto_merge_workflow,
    }

    for key, value in updates.items():
        if value is None:
            continue
        if isinstance(value, bool):
            str_val = "true" if value else "false"
        else:
            str_val = str(value)
        os.environ[key] = str_val
        set_key(dotenv_path, key, str_val)

    console.print("Current config:")
    console.print(f"  verbose: {CONFIG['verbose']}")
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
    format: List[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s). Can be passed multiple times.",
    ),
) -> None:
    """Convert files using Docling."""
    fmts = format or _parse_env_formats() or [OutputFormat.MARKDOWN]
    if not CONFIG["verbose"]:
        warnings.filterwarnings("ignore")
    if source.startswith(("http://", "https://")):
        results = convert_path(source, fmts)
    else:
        results = convert_path(Path(source), fmts)
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
    format: List[OutputFormat] = typer.Option(
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


__all__ = ["app", "analyze_doc", "validate_doc", "convert_path", "validate_file", "run_prompt", "main"]


def _interactive_shell() -> None:  # pragma: no cover - CLI utility
    try:
        _print_banner()
        app(prog_name="cli.py", args=["--help"])
    except SystemExit:
        pass
    while True:
        try:
            command = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not command:
            continue
        if command.lower() in {"exit", "quit"}:
            break
        if command.startswith("cd"):
            parts = command.split(maxsplit=1)
            target = Path(parts[1]).expanduser() if len(parts) > 1 else Path.home()
            try:
                os.chdir(target)
            except OSError as exc:
                console.print(f"[red]{exc}[/red]")
            continue
        full_cmd = command
        if CONFIG["verbose"]:
            full_cmd += " --verbose"
        try:
            app(prog_name="cli.py", args=shlex.split(full_cmd))
        except SystemExit:
            pass
        except Exception as exc:  # pragma: no cover - runtime error display
            if CONFIG["verbose"]:
                traceback.print_exc()
            else:
                console.print(f"[red]{exc}[/red]")


def main() -> None:
    """Entry point for running the CLI as a script."""
    if len(sys.argv) > 1:
        _print_banner()
        args = sys.argv[1:]
        if CONFIG["verbose"] and "--verbose" not in args and "-v" not in args:
            args.append("--verbose")
        try:
            app(prog_name="cli.py", args=args)
        except Exception as exc:  # pragma: no cover - runtime error display
            if CONFIG["verbose"]:
                traceback.print_exc()
            else:
                console.print(f"[red]{exc}[/red]")
    else:
        _interactive_shell()
