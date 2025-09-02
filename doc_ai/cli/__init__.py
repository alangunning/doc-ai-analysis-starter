from __future__ import annotations

import os
import shlex
import sys
import traceback
from pathlib import Path
from typing import List, Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from .common import (
    analyze_doc,
    converted_suffix,
    infer_format,
    parse_env_formats,
    print_banner,
    validate_doc,
)
from doc_ai.converter import OutputFormat, convert_path
from doc_ai.github import build_vector_store, run_prompt, validate_file

load_dotenv()

console = Console()
app = typer.Typer(help="Orchestrate conversion, validation, analysis and embedding generation.")

SETTINGS = {"verbose": os.getenv("VERBOSE", "").lower() in {"1", "true", "yes"}}

_print_banner = print_banner


def _interactive_shell() -> None:  # pragma: no cover - CLI utility
    try:
        _print_banner()
        app(prog_name="cli", args=["--help"])
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
        if SETTINGS["verbose"]:
            full_cmd += " --verbose"
        try:
            app(prog_name="cli", args=shlex.split(full_cmd))
        except SystemExit:
            pass
        except Exception as exc:  # pragma: no cover - runtime error display
            if SETTINGS["verbose"]:
                traceback.print_exc()
            else:
                console.print(f"[red]{exc}[/red]")


@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")):
    SETTINGS["verbose"] = verbose


CONFIG_DEFAULTS = {
    "OUTPUT_FORMATS": "markdown,html,json,text,doctags",
    "OPENAI_API_KEY": "",
    "GITHUB_TOKEN": "",
    "BASE_MODEL_URL": "https://models.github.ai/inference",
    "VALIDATE_BASE_MODEL_URL": "https://api.openai.com/v1",
    "VALIDATE_MODEL": "gpt-4.1",
    "ANALYZE_MODEL": "gpt-4.1",
    "ANALYZE_BASE_MODEL_URL": "https://models.github.ai/inference",
    "EMBED_MODEL": "openai/text-embedding-3-small",
    "VECTOR_BASE_MODEL_URL": "https://models.github.ai/inference",
}


@app.command()
def settings(verbose: bool = typer.Option(None, "--verbose/--no-verbose", help="Toggle verbose error output")) -> None:
    if verbose is not None:
        SETTINGS["verbose"] = verbose
    table = Table(title="Current settings")
    table.add_column("Name")
    table.add_column("Current")
    table.add_column("Default")
    table.add_row("verbose", str(SETTINGS["verbose"]), "false")
    for name, default in CONFIG_DEFAULTS.items():
        table.add_row(name, os.getenv(name, ""), default)
    console.print(table)


@app.command()
def convert(
    source: str = typer.Argument(..., help="Path or URL to raw document or folder"),
    format: List[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s). Can be passed multiple times. [env: OUTPUT_FORMATS]",
        show_default=False,
    ),
) -> None:
    env_fmts = parse_env_formats()
    fmts = format or env_fmts or [OutputFormat.MARKDOWN]
    if not SETTINGS["verbose"]:
        import warnings
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
    rendered: Path | None = typer.Argument(None, help="Path to converted file"),
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f"),
    prompt: Optional[Path] = typer.Option(None, "--prompt", help="Prompt file"),
    model: Optional[str] = typer.Option(
        os.getenv("VALIDATE_MODEL"),
        "--model",
        envvar="VALIDATE_MODEL",
        help="Model name",
        show_default=True,
    ),
    base_model_url: Optional[str] = typer.Option(
        os.getenv("VALIDATE_BASE_MODEL_URL") or os.getenv("BASE_MODEL_URL"),
        "--base-model-url",
        envvar="VALIDATE_BASE_MODEL_URL",
        help="Model base URL",
        show_default=True,
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    log_file: Optional[Path] = typer.Option(None, "--log-file", help="Write request/response details to this file"),
) -> None:
    import logging
    from rich.logging import RichHandler

    logger: logging.Logger | None = None
    log_path = log_file
    console_obj = Console()
    if verbose or log_path is not None:
        logger = logging.getLogger("doc_ai.validate")
        logger.setLevel(logging.DEBUG)
        if verbose:
            sh = RichHandler(console=console_obj, show_time=False)
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
        rendered = raw.with_name(raw.name + converted_suffix(used_fmt))
    else:
        used_fmt = fmt or infer_format(rendered)
    from .common import validate_doc
    validate_doc(
        raw,
        rendered,
        used_fmt,
        prompt,
        model,
        base_model_url,
        show_progress=True,
        logger=logger,
        console_obj=console_obj,
    )


@app.command()
def analyze(
    source: Path = typer.Argument(..., help="Raw or converted document"),
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f", help="Format of converted file"),
    prompt: Path | None = typer.Option(None, "--prompt", "-p", help="Prompt file"),
    output: Optional[Path] = typer.Option(None, "--output", help="Optional output file"),
    model: Optional[str] = typer.Option(
        os.getenv("ANALYZE_MODEL"),
        "--model",
        envvar="ANALYZE_MODEL",
        help="Model name",
        show_default=True,
    ),
    base_model_url: Optional[str] = typer.Option(
        os.getenv("ANALYZE_BASE_MODEL_URL") or os.getenv("BASE_MODEL_URL"),
        "--base-model-url",
        envvar="ANALYZE_BASE_MODEL_URL",
        help="Model base URL",
        show_default=True,
    ),
) -> None:
    markdown_doc = source
    if ".converted" not in "".join(markdown_doc.suffixes):
        used_fmt = fmt or OutputFormat.MARKDOWN
        markdown_doc = source.with_name(source.name + converted_suffix(used_fmt))
    analyze_doc(markdown_doc, prompt, output, model, base_model_url)


@app.command()
def embed(
    source: Path = typer.Argument(..., help="Directory containing Markdown files"),
    model: Optional[str] = typer.Option(
        os.getenv("EMBED_MODEL"),
        "--model",
        envvar="EMBED_MODEL",
        help="Embedding model",
        show_default=True,
    ),
    base_model_url: Optional[str] = typer.Option(
        os.getenv("VECTOR_BASE_MODEL_URL") or os.getenv("BASE_MODEL_URL"),
        "--base-model-url",
        envvar="VECTOR_BASE_MODEL_URL",
        help="Embedding base URL",
        show_default=True,
    ),
) -> None:
    if model:
        os.environ["EMBED_MODEL"] = model
    if base_model_url:
        os.environ["VECTOR_BASE_MODEL_URL"] = base_model_url
    build_vector_store(source)


@app.command("pipeline")
def pipeline(
    source: Path = typer.Argument(..., help="Directory with raw documents"),
    prompt: Path = typer.Option(Path(".github/prompts/doc-analysis.analysis.prompt.yaml"), help="Analysis prompt file"),
    format: List[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s) for conversion. [env: OUTPUT_FORMATS]",
        show_default=False,
    ),
    model: Optional[str] = typer.Option(
        os.getenv("ANALYZE_MODEL"),
        "--model",
        envvar="ANALYZE_MODEL",
        help="Model name",
        show_default=True,
    ),
    base_model_url: Optional[str] = typer.Option(
        os.getenv("ANALYZE_BASE_MODEL_URL") or os.getenv("BASE_MODEL_URL"),
        "--base-model-url",
        envvar="ANALYZE_BASE_MODEL_URL",
        help="Model base URL",
        show_default=True,
    ),
) -> None:
    env_fmts = parse_env_formats()
    fmts = format or env_fmts or [OutputFormat.MARKDOWN]
    convert_path(source, fmts)
    validation_prompt = Path(".github/prompts/validate-output.validate.prompt.yaml")
    for raw_file in source.rglob("*"):
        if not raw_file.is_file():
            continue
        md_file = raw_file.with_name(raw_file.name + converted_suffix(OutputFormat.MARKDOWN))
        if md_file.exists():
            from .common import validate_doc
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
    "print_banner",
    "SETTINGS",
    "validate_doc",
    "analyze_doc",
    "run_prompt",
    "validate_file",
    "_interactive_shell",
    "_print_banner",
]
