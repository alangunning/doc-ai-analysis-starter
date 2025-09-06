from __future__ import annotations

from pathlib import Path
from typing import Optional, List
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import typer
from rich.progress import Progress

from doc_ai.converter import OutputFormat
from .utils import (
    parse_config_formats as _parse_config_formats,
    resolve_bool,
    resolve_int,
    resolve_str,
    suffix as _suffix,
    prompt_for_missing,
)
from . import RAW_SUFFIXES, ModelName, _validate_prompt

import re

logger = logging.getLogger(__name__)


class PipelineStep(str, Enum):
    """Named steps within the document pipeline."""

    CONVERT = "convert"
    VALIDATE = "validate"
    ANALYZE = "analyze"
    EMBED = "embed"


def _discover_topics(doc_dir: Path) -> list[str | None]:
    """Return analysis topics available for a document directory.

    Topics are inferred from prompt filenames matching
    ``analysis_<topic>.prompt.yaml`` or ``<type>.analysis.<topic>.prompt.yaml``.
    If no topic-specific prompts are found but generic analysis prompts exist,
    a ``None`` topic is returned.
    """
    topics: list[str | None] = []
    for p in doc_dir.glob("analysis_*.prompt.yaml"):
        m = re.match(r"analysis_(.+)\.prompt\.yaml$", p.name)
        if m:
            topics.append(m.group(1))
    prefix = f"{doc_dir.name}.analysis."
    for p in doc_dir.glob(f"{doc_dir.name}.analysis.*.prompt.yaml"):
        if p.name.startswith(prefix) and p.name.endswith(".prompt.yaml"):
            topic = p.name[len(prefix) : -len(".prompt.yaml")]
            topics.append(topic)
    if (doc_dir / "analysis.prompt.yaml").exists() or (
        doc_dir / f"{doc_dir.name}.analysis.prompt.yaml"
    ).exists():
        topics.append(None)
    if not topics:
        topics.append(None)
    seen = []
    for t in topics:
        if t not in seen:
            seen.append(t)
    return seen


def pipeline(
    source: Path,
    prompt: Path | None = None,
    format: list[OutputFormat] | None = None,
    model: Optional[ModelName] = None,
    base_model_url: Optional[str] = None,
    fail_fast: bool = True,
    show_cost: bool = False,
    estimate: bool = True,
    workers: int = 1,
    force: bool = False,
    dry_run: bool = False,
    resume_from: PipelineStep = PipelineStep.CONVERT,
    skip: list[PipelineStep] | None = None,
    topics: list[str] | None = None,
) -> None:
    """Run the full pipeline: convert, validate, analyze, and embed."""
    from . import (
        convert_path as _convert_path,
        validate_doc as _validate_doc,
        analyze_doc as _analyze_doc,
        build_vector_store as _build_vector_store,
    )

    fmts = format or [OutputFormat.MARKDOWN]
    validation_prompt = Path(".github/prompts/validate-output.validate.prompt.yaml")
    failures: list[tuple[str, Path, Exception]] = []
    lock = Lock()
    skip_set = set(skip or [])
    order = [
        PipelineStep.CONVERT,
        PipelineStep.VALIDATE,
        PipelineStep.ANALYZE,
        PipelineStep.EMBED,
    ]
    resume_idx = order.index(resume_from)

    def should_run(step: PipelineStep) -> bool:
        return order.index(step) >= resume_idx and step not in skip_set

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
            if should_run(PipelineStep.CONVERT):
                logger.info(
                    "Would convert %s to %s", raw_file, ", ".join(f.value for f in fmts)
                )
            md_file = raw_file.with_name(raw_file.name + _suffix(OutputFormat.MARKDOWN))
            if should_run(PipelineStep.VALIDATE):
                logger.info("Would validate %s", md_file)
            if should_run(PipelineStep.ANALYZE):
                topic_list = topics if topics else _discover_topics(md_file.parent)
                for tp in topic_list:
                    if tp is None:
                        logger.info("Would analyze %s", md_file)
                    else:
                        logger.info("Would analyze %s (topic: %s)", md_file, tp)
            return
        if should_run(PipelineStep.CONVERT):
            try:
                _convert_path(raw_file, fmts, force=force)
            except Exception as exc:  # pragma: no cover - error handling
                local_failures.append(("conversion", raw_file, exc))
                logger.error("[red]Conversion failed for %s: %s[/red]", raw_file, exc)
        md_file = raw_file.with_name(raw_file.name + _suffix(OutputFormat.MARKDOWN))
        if md_file.exists() and should_run(PipelineStep.VALIDATE):
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
                logger.error("[red]Validation failed for %s: %s[/red]", raw_file, exc)
        if (
            md_file.exists()
            and should_run(PipelineStep.ANALYZE)
            and not (fail_fast and local_failures)
        ):
            topic_list = topics if topics else _discover_topics(md_file.parent)
            for tp in topic_list:
                try:
                    _analyze_doc(
                        md_file,
                        prompt=prompt if tp is None else None,
                        model=model,
                        base_url=base_model_url,
                        show_cost=show_cost,
                        estimate=estimate,
                        topic=tp,
                        force=force,
                    )
                except Exception as exc:  # pragma: no cover - error handling
                    local_failures.append(("analysis", md_file, exc))
                    logger.error("[red]Analysis failed for %s: %s[/red]", md_file, exc)
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

    if fail_fast and failures:
        raise typer.Exit(1)

    if failures:
        logger.error("[bold red]Failures encountered during pipeline:[/bold red]")
        for step, path, exc in failures:
            logger.error("- %s %s: %s", step, path, exc)
        raise typer.Exit(code=1)

    if not failures and should_run(PipelineStep.EMBED):
        if dry_run:
            logger.info("Would build vector store for %s", source)
        else:
            _build_vector_store(source, workers=workers)


app = typer.Typer(
    invoke_without_command=True,
    help="Run the full pipeline: convert, validate, analyze, and embed.",
)


@app.callback()
def _entrypoint(
    ctx: typer.Context,
    source: Path | None = typer.Argument(None, help="Directory with raw documents"),
    prompt: Path | None = typer.Option(
        None,
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
    resume_from: PipelineStep = typer.Option(
        PipelineStep.CONVERT,
        "--resume-from",
        help="Resume processing from a given step (convert, validate, analyze, embed)",
        case_sensitive=False,
    ),
    skip: list[PipelineStep] = typer.Option(
        None,
        "--skip",
        help="Skip one or more steps (convert, validate, analyze, embed)",
        case_sensitive=False,
    ),
    topic: List[str] = typer.Option(
        None,
        "--topic",
        "-t",
        help="Analysis topic(s) to run; defaults to all discovered",
    ),
) -> None:
    """Run the full pipeline: convert, validate, analyze, and embed.

    Examples:
        doc-ai pipeline docs/
    """
    if ctx.obj is None:
        ctx.obj = {}
    source = prompt_for_missing(source, "Directory with raw documents", path=True)
    if source is None:
        raise typer.BadParameter("SOURCE is required")
    cfg = ctx.obj.get("config", {})
    format = format or _parse_config_formats(cfg)
    model = resolve_str(ctx, "model", model, cfg, "MODEL")
    base_model_url = resolve_str(
        ctx, "base_model_url", base_model_url, cfg, "BASE_MODEL_URL"
    )
    fail_fast = resolve_bool(ctx, "fail_fast", fail_fast, cfg, "FAIL_FAST")
    show_cost = resolve_bool(ctx, "show_cost", show_cost, cfg, "SHOW_COST")
    estimate = resolve_bool(ctx, "estimate", estimate, cfg, "ESTIMATE")
    workers = resolve_int(ctx, "workers", workers, cfg, "WORKERS")
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")
    dry_run = resolve_bool(ctx, "dry_run", dry_run, cfg, "DRY_RUN")
    resume_from_val = resolve_str(
        ctx, "resume_from", resume_from.value, cfg, "RESUME_FROM"
    )
    try:
        resume_from = PipelineStep(resume_from_val)
    except ValueError as exc:
        raise typer.BadParameter(f"Invalid resume step '{resume_from_val}'") from exc
    kwargs = dict(
        source=source,
        prompt=prompt,
        format=format,
        model=model,
        base_model_url=base_model_url,
        fail_fast=fail_fast,
        show_cost=show_cost,
        estimate=estimate,
        workers=workers,
        force=force,
        dry_run=dry_run,
        resume_from=resume_from,
        skip=skip,
    )
    if topic:
        kwargs["topics"] = list(topic)
    pipeline(**kwargs)
