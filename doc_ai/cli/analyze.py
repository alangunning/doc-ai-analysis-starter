from __future__ import annotations

from pathlib import Path
from typing import Optional
import logging

import typer

from doc_ai.converter import OutputFormat
from doc_ai.logging import configure_logging
from .utils import analyze_doc, suffix as _suffix, resolve_bool, resolve_str
from . import ModelName, _validate_prompt

logger = logging.getLogger(__name__)

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
    force: bool = typer.Option(
        False,
        "--force",
        help="Re-run analysis even if metadata is present",
        is_flag=True,
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
) -> None:
    """Run an analysis prompt against a converted document.

    Examples:
        doc-ai analyze report.md --verbose
        doc-ai --log-file run.log analyze report.md
    """
    if ctx.obj is None:
        ctx.obj = {}
    if any(opt is not None for opt in (verbose, log_level, log_file)):
        level_name = "DEBUG" if verbose else log_level or logging.getLevelName(
            logging.getLogger().level
        )
        configure_logging(level_name, log_file)
        ctx.obj["verbose"] = logging.getLogger().level <= logging.DEBUG
        ctx.obj["log_level"] = level_name
        ctx.obj["log_file"] = log_file
    cfg = ctx.obj.get("config", {})
    model = resolve_str(ctx, "model", model, cfg, "MODEL")
    base_model_url = resolve_str(ctx, "base_model_url", base_model_url, cfg, "BASE_MODEL_URL")
    require_json = resolve_bool(ctx, "require_json", require_json, cfg, "REQUIRE_STRUCTURED")
    show_cost = resolve_bool(ctx, "show_cost", show_cost, cfg, "SHOW_COST")
    estimate = resolve_bool(ctx, "estimate", estimate, cfg, "ESTIMATE")
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")
    markdown_doc = source
    if ".converted" not in "".join(markdown_doc.suffixes):
        used_fmt = fmt or OutputFormat.MARKDOWN
        markdown_doc = source.with_name(source.name + _suffix(used_fmt))
    try:
        analyze_doc(
            markdown_doc,
            prompt,
            output,
            model,
            base_model_url,
            require_json,
            show_cost,
            estimate,
            force=force,
        )
    except ValueError as exc:
        logger.error("[red]%s[/red]", exc)
        raise typer.Exit(1) from exc
