from __future__ import annotations

from pathlib import Path
from typing import Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import typer
from rich.progress import Progress

from doc_ai.converter import OutputFormat
from doc_ai.logging import configure_logging
from .utils import parse_env_formats as _parse_env_formats, suffix as _suffix
from . import RAW_SUFFIXES, ModelName, _validate_prompt

logger = logging.getLogger(__name__)


def pipeline(
    source: Path,
    prompt: Path = Path(".github/prompts/doc-analysis.analysis.prompt.yaml"),
    format: list[OutputFormat] | None = None,
    model: Optional[ModelName] = None,
    base_model_url: Optional[str] = None,
    fail_fast: bool = True,
    show_cost: bool = False,
    estimate: bool = True,
    workers: int = 1,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    """Run the full pipeline: convert, validate, analyze, and embed."""
    from . import (
        convert_path as _convert_path,
        validate_doc as _validate_doc,
        analyze_doc as _analyze_doc,
        build_vector_store as _build_vector_store,
    )

    fmts = format or _parse_env_formats() or [OutputFormat.MARKDOWN]
    validation_prompt = Path(
        ".github/prompts/validate-output.validate.prompt.yaml"
    )
    failures: list[tuple[str, Path, Exception]] = []
    lock = Lock()

    class PipelineError(Exception):
        def __init__(self, step: str, path: Path, exc: Exception) -> None:
            super().__init__(str(exc))
            self.step = step
            self.path = path
            self.exc = exc

    raw_files = [
        f
        for ext in RAW_SUFFIXES
        for f in source.rglob(f"*{ext}")
        if f.is_file() and not any(".converted" in part for part in f.parts)
    ]

    def process(raw_file: Path) -> None:
        local_failures: list[tuple[str, Path, Exception]] = []
        if dry_run:
            logger.info("Would convert %s to %s", raw_file, ", ".join(f.value for f in fmts))
            md_file = raw_file.with_name(raw_file.name + _suffix(OutputFormat.MARKDOWN))
            logger.info("Would validate %s", md_file)
            logger.info("Would analyze %s", md_file)
            return
        try:
            _convert_path(raw_file, fmts, force=force)
        except Exception as exc:  # pragma: no cover - error handling
            local_failures.append(("conversion", raw_file, exc))
            logger.error(
                "[red]Conversion failed for %s: %s[/red]", raw_file, exc
            )
        md_file = raw_file.with_name(raw_file.name + _suffix(OutputFormat.MARKDOWN))
        if md_file.exists():
            try:
                _validate_doc(
                    raw_file,
                    md_file,
                    OutputFormat.MARKDOWN,
                    validation_prompt,
                    model,
                    base_model_url,
                    force=force,
                )
            except Exception as exc:  # pragma: no cover - error handling
                local_failures.append(("validation", raw_file, exc))
                logger.error(
                    "[red]Validation failed for %s: %s[/red]", raw_file, exc
                )
            if not (fail_fast and local_failures):
                try:
                    _analyze_doc(
                        md_file,
                        prompt=prompt,
                        model=model,
                        base_url=base_model_url,
                        show_cost=show_cost,
                        estimate=estimate,
                        force=force,
                    )
                except Exception as exc:  # pragma: no cover - error handling
                    local_failures.append(("analysis", md_file, exc))
                    logger.error(
                        "[red]Analysis failed for %s: %s[/red]", md_file, exc
                    )
        if local_failures:
            if fail_fast:
                step, path, exc = local_failures[0]
                raise PipelineError(step, path, exc) from exc
            with lock:
                failures.extend(local_failures)

    with Progress(transient=True) as progress:
        task = progress.add_task("Processing documents", total=len(raw_files))
        if fail_fast:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                for raw_file in raw_files:
                    fut = executor.submit(process, raw_file)
                    try:
                        fut.result()
                    except PipelineError as pe:  # pragma: no cover - error handling
                        failures.append((pe.step, pe.path, pe.exc))
                        break
                    finally:
                        progress.advance(task)
                    if failures:
                        break
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(process, f): f for f in raw_files}
                for fut in as_completed(futures):
                    fut.result()
                    progress.advance(task)
    if dry_run:
        logger.info("Would build vector store for %s", source)
    else:
        _build_vector_store(source, workers=workers)
    if failures:
        logger.error("[bold red]Failures encountered during pipeline:[/bold red]")
        for step, path, exc in failures:
            logger.error("- %s %s: %s", step, path, exc)
        raise typer.Exit(code=1)


app = typer.Typer(invoke_without_command=True, help="Run the full pipeline: convert, validate, analyze, and embed.")


@app.callback()
def _entrypoint(
    ctx: typer.Context,
    source: Path = typer.Argument(..., help="Directory with raw documents"),
    prompt: Path = typer.Option(
        Path(".github/prompts/doc-analysis.analysis.prompt.yaml"),
        help="Analysis prompt file",
        callback=_validate_prompt,
    ),
    format: list[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s) for conversion",
    ),
    model: Optional[ModelName] = typer.Option(
        None,
        "--model",
        help="Model name override",
    ),
    base_model_url: Optional[str] = typer.Option(
        None, "--base-model-url", help="Model base URL override"
    ),
    fail_fast: bool = typer.Option(
        True,
        "--fail-fast/--keep-going",
        help="Stop processing on first validation or analysis failure",
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
    workers: int = typer.Option(
        1,
        "--workers",
        "-w",
        help="Number of worker threads",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Re-run steps even if metadata indicates completion",
        is_flag=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Log steps without executing conversion, validation, or analysis",
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
    """Run the full pipeline: convert, validate, analyze, and embed.

    Examples:
        doc-ai pipeline docs/ --verbose
        doc-ai --log-file pipeline.log pipeline docs/
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
    pipeline(
        source,
        prompt,
        format,
        model,
        base_model_url,
        fail_fast,
        show_cost,
        estimate,
        workers,
        force,
        dry_run,
    )
