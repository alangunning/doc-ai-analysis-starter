from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from doc_ai.converter import OutputFormat
from .utils import parse_env_formats as _parse_env_formats, suffix as _suffix
from . import RAW_SUFFIXES, ModelName, _validate_prompt, console


def pipeline(
    source: Path,
    prompt: Path = Path(".github/prompts/doc-analysis.analysis.prompt.yaml"),
    format: list[OutputFormat] | None = None,
    model: Optional[ModelName] = None,
    base_model_url: Optional[str] = None,
    fail_fast: bool = True,
    show_cost: bool = False,
    estimate: bool = True,
) -> None:
    """Run the full pipeline: convert, validate, analyze, and embed."""
    from . import (
        convert_path as _convert_path,
        validate_doc as _validate_doc,
        analyze_doc as _analyze_doc,
        build_vector_store as _build_vector_store,
    )

    fmts = format or _parse_env_formats() or [OutputFormat.MARKDOWN]
    _convert_path(source, fmts)
    validation_prompt = Path(
        ".github/prompts/validate-output.validate.prompt.yaml"
    )
    failures: list[tuple[str, Path, Exception]] = []
    candidates = (
        f
        for ext in RAW_SUFFIXES
        for f in source.rglob(f"*{ext}")
        if not any(".converted" in part for part in f.parts)
    )
    for raw_file in candidates:
        if not raw_file.is_file():
            continue
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
                )
            except Exception as exc:  # pragma: no cover - error handling
                failures.append(("validation", raw_file, exc))
                console.print(
                    f"[red]Validation failed for {raw_file}: {exc}[/red]"
                )
                if fail_fast:
                    break
            try:
                _analyze_doc(
                    md_file,
                    prompt=prompt,
                    model=model,
                    base_url=base_model_url,
                    show_cost=show_cost,
                    estimate=estimate,
                )
            except Exception as exc:  # pragma: no cover - error handling
                failures.append(("analysis", md_file, exc))
                console.print(
                    f"[red]Analysis failed for {md_file}: {exc}[/red]"
                )
                if fail_fast:
                    break
    _build_vector_store(source)
    if failures:
        console.print("[bold red]Failures encountered during pipeline:[/bold red]")
        for step, path, exc in failures:
            console.print(f"- {step} {path}: {exc}")
        raise typer.Exit(code=1)


app = typer.Typer(invoke_without_command=True, help="Run the full pipeline: convert, validate, analyze, and embed.")


@app.callback()
def _entrypoint(
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
) -> None:
    pipeline(
        source,
        prompt,
        format,
        model,
        base_model_url,
        fail_fast,
        show_cost,
        estimate,
    )
