from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from doc_ai.converter import OutputFormat
from .utils import analyze_doc, suffix as _suffix
from . import ModelName, _validate_prompt

app = typer.Typer(invoke_without_command=True, help="Run an analysis prompt against a converted document.")


@app.callback()
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
        callback=_validate_prompt,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Optional output file; defaults to <doc>.analysis.json",
    ),
    model: Optional[ModelName] = typer.Option(
        None,
        "--model",
        help="Model name override",
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
    show_cost: bool = typer.Option(
        False,
        "--show-cost",
        help="Display token cost estimates",
        is_flag=True,
    ),
    estimate: bool = typer.Option(
        True,
        "--estimate/--no-estimate",
        help="Print pre-run cost estimate",
    ),
    fail_fast: bool = typer.Option(
        True,
        "--fail-fast/--keep-going",
        help="Stop processing on first validation or analysis failure",
    ),
) -> None:
    """Run an analysis prompt against a converted document."""
    markdown_doc = source
    if ".converted" not in "".join(markdown_doc.suffixes):
        used_fmt = fmt or OutputFormat.MARKDOWN
        markdown_doc = source.with_name(source.name + _suffix(used_fmt))
    analyze_doc(
        markdown_doc,
        prompt,
        output,
        model,
        base_model_url,
        require_json,
        show_cost,
        estimate,
    )
