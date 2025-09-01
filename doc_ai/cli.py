#!/usr/bin/env python3
"""CLI orchestrator for AI document analysis pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import os
import sys
import shlex
import json

import typer
from rich.console import Console
from dotenv import load_dotenv

# Ensure project root is on sys.path when running as a script.
if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from doc_ai.converter import OutputFormat, convert_path, suffix_for_format
from doc_ai.github import build_vector_store, run_prompt, validate_file
from doc_ai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)

load_dotenv()

console = Console()
app = typer.Typer(
    help="Orchestrate conversion, validation, analysis and embedding generation."
)

ASCII_ART = r"""
 ____   ___   ____      _    ___    ____ _     ___
|  _ \ / _ \ / ___|    / \  |_ _|  / ___| |   |_ _|
| | | | | | | |       / _ \  | |  | |   | |    | |
| |_| | |_| | |___   / ___ \ | |  | |___| |___ | |
|____/ \___/ \____| /_/   \_\___|  \____|_____|___|
"""

CONFIG_PATH = Path.home() / ".doc_ai_shell_config.json"
GLOBAL_OPTION_COMMANDS = {
    "help": "--help",
    "install-completion": "--install-completion",
    "show-completion": "--show-completion",
}


def _load_shell_config() -> dict[str, str]:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_shell_config(cfg: dict[str, str]) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

def _print_banner() -> None:  # pragma: no cover - visual flair only
    console.print(f"[bold green]{ASCII_ART}[/bold green]")

def _suffix(fmt: OutputFormat) -> str:
    return f".converted{suffix_for_format(fmt)}"


def _parse_env_formats() -> List[OutputFormat] | None:
    """Return formats from OUTPUT_FORMATS env var if set."""

    env_val = os.getenv("OUTPUT_FORMATS")
    if not env_val:
        return None
    formats: List[OutputFormat] = []
    for val in env_val.split(","):
        try:
            formats.append(OutputFormat(val.strip()))
        except ValueError as exc:
            valid = ", ".join(f.value for f in OutputFormat)
            raise typer.BadParameter(
                f"Invalid output format '{val}'. Choose from: {valid}"
            ) from exc
    return formats


def validate_doc(
    raw: Path,
    rendered: Path,
    fmt: OutputFormat | None = None,
    prompt: Path = Path(".github/prompts/validate-output.prompt.yaml"),
    model: str | None = None,
    base_url: str | None = None,
) -> None:
    meta = load_metadata(raw)
    file_hash = compute_hash(raw)
    if meta.blake2b == file_hash and is_step_done(meta, "validation"):
        return
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}
    if fmt is None:
        mapping = {
            ".md": OutputFormat.MARKDOWN,
            ".html": OutputFormat.HTML,
            ".json": OutputFormat.JSON,
            ".txt": OutputFormat.TEXT,
            ".doctags": OutputFormat.DOCTAGS,
        }
        fmt = mapping.get(rendered.suffix)
        if fmt is None:
            valid = ", ".join(mapping.keys())
            raise typer.BadParameter(
                f"Unknown file extension '{rendered.suffix}'. Expected one of: {valid}"
            )
    verdict = validate_file(
        raw,
        rendered,
        fmt,
        prompt,
        model=model,
        base_url=base_url,
    )
    if not verdict.get("match", False):
        raise RuntimeError(f"Mismatch detected: {verdict}")
    mark_step(meta, "validation")
    save_metadata(raw, meta)


def analyze_doc(
    prompt: Path,
    markdown_doc: Path,
    output: Path | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> None:
    prompt_name = prompt.name.replace(".prompt.yaml", "")
    step_name = "analysis"
    meta = load_metadata(markdown_doc)
    file_hash = compute_hash(markdown_doc)
    if meta.blake2b == file_hash and is_step_done(meta, step_name):
        return
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}
    result = run_prompt(
        prompt,
        markdown_doc.read_text(),
        model=model,
        base_url=base_url,
    )
    out_path = (
        output if output else markdown_doc.with_suffix(f".{prompt_name}.json")
    )
    out_path.write_text(result + "\n", encoding="utf-8")
    mark_step(meta, step_name, outputs=[out_path.name])
    save_metadata(markdown_doc, meta)


@app.command()
def convert(
    source: Path = typer.Argument(..., help="Path to raw document or folder"),
    format: List[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s). Can be passed multiple times.",
    ),
) -> None:
    """Convert files using Docling."""
    env_fmts = _parse_env_formats()
    fmts = format or env_fmts or [OutputFormat.MARKDOWN]
    convert_path(source, fmts)


@app.command()
def validate(
    raw: Path = typer.Argument(..., help="Path to raw document"),
    rendered: Path = typer.Argument(..., help="Path to converted file"),
    fmt: Optional[OutputFormat] = typer.Option(None, "--format"),
    prompt: Path = typer.Option(
        Path(".github/prompts/validate-output.prompt.yaml"),
        help="Prompt file",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model name override"
    ),
    base_model_url: Optional[str] = typer.Option(
        None, "--base-model-url", help="Model base URL override"
    ),
) -> None:
    """Validate converted output against the original file."""
    validate_doc(raw, rendered, fmt, prompt, model, base_model_url)


@app.command()
def analyze(
    prompt: Path = typer.Argument(..., help="Prompt file"),
    markdown_doc: Path = typer.Argument(..., help="Markdown document"),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Optional output file; defaults to <doc>.<prompt>.json",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model name override"
    ),
    base_model_url: Optional[str] = typer.Option(
        None, "--base-model-url", help="Model base URL override"
    ),
) -> None:
    """Run an analysis prompt against a Markdown document."""
    analyze_doc(prompt, markdown_doc, output, model, base_model_url)


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
        Path(".github/prompts/doc-analysis.prompt.yaml"),
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
    env_fmts = _parse_env_formats()
    fmts = format or env_fmts or [OutputFormat.MARKDOWN]
    convert_path(source, fmts)
    validation_prompt = Path(".github/prompts/validate-output.prompt.yaml")
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
            analyze_doc(prompt, md_file, model=model, base_url=base_model_url)
    build_vector_store(source)


__all__ = ["app"]


def _interactive_shell() -> None:  # pragma: no cover - CLI utility
    cfg = _load_shell_config()
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
        try:
            tokens = shlex.split(command)
        except ValueError:
            console.print("Invalid command")
            continue
        if not tokens:
            continue
        cmd = tokens[0].lower()
        if cmd == "config":
            if len(tokens) == 1 or tokens[1] == "show":
                console.print(cfg)
            elif len(tokens) >= 4 and tokens[1] == "set":
                cfg[tokens[2].lower()] = tokens[3]
                _save_shell_config(cfg)
                console.print(f"Set {tokens[2]} = {tokens[3]}")
            else:
                console.print("Usage: config set <key> <value> | config show")
            continue
        if cmd in GLOBAL_OPTION_COMMANDS:
            app(prog_name="cli.py", args=[GLOBAL_OPTION_COMMANDS[cmd]])
            continue
        resolved = []
        for tok in tokens:
            for key, value in cfg.items():
                placeholder = f"[{key.upper()}]"
                if placeholder in tok:
                    tok = tok.replace(placeholder, value)
            resolved.append(tok)
        try:
            app(prog_name="cli.py", args=resolved)
        except SystemExit:
            pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        _print_banner()
        app()
    else:
        _interactive_shell()
