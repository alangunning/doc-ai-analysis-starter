"""Shared utilities for doc_ai CLI."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping, TypeVar
import logging
import os
import re
import json
import functools
from datetime import datetime, timezone

import click
import typer
from rich.console import Console
from dotenv import dotenv_values
from click.core import ParameterSource

from doc_ai.converter import OutputFormat, suffix_for_format
from doc_ai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)

logger = logging.getLogger(__name__)

# Mapping of file extensions to output formats used across commands
EXTENSION_MAP = {
    ".md": OutputFormat.MARKDOWN,
    ".html": OutputFormat.HTML,
    ".json": OutputFormat.JSON,
    ".txt": OutputFormat.TEXT,
    ".doctags": OutputFormat.DOCTAGS,
    ".csv": OutputFormat.CSV,
    ".summary.txt": OutputFormat.SUMMARY_TXT,
}


def suffix(fmt: OutputFormat) -> str:
    """Return the standard suffix for a converted file."""
    return f".converted{suffix_for_format(fmt)}"


def infer_format(path: Path) -> OutputFormat:
    """Infer an output format from a file extension."""
    if path.name.endswith(".summary.txt"):
        return OutputFormat.SUMMARY_TXT
    try:
        return EXTENSION_MAP[path.suffix.lower()]
    except KeyError as exc:
        valid = ", ".join(EXTENSION_MAP.keys())
        raise typer.BadParameter(
            f"Unknown file extension '{path.suffix}'. Expected one of: {valid}"
        ) from exc


def parse_env_formats() -> list[OutputFormat] | None:
    """Return formats from OUTPUT_FORMATS env var if set."""
    env_val = os.getenv("OUTPUT_FORMATS")
    if not env_val:
        return None
    formats: list[OutputFormat] = []
    for val in env_val.split(","):
        try:
            formats.append(OutputFormat(val.strip()))
        except ValueError as exc:
            valid = ", ".join(f.value for f in OutputFormat)
            raise typer.BadParameter(
                f"Invalid output format '{val}'. Choose from: {valid}"
            ) from exc
    return formats


T = TypeVar("T")


def parse_config_formats(cfg: Mapping[str, str]) -> list[OutputFormat] | None:
    """Return formats from config mapping if set."""
    env_val = cfg.get("OUTPUT_FORMATS")
    if not env_val:
        return None
    formats: list[OutputFormat] = []
    for val in env_val.split(","):
        try:
            formats.append(OutputFormat(val.strip()))
        except ValueError as exc:
            valid = ", ".join(f.value for f in OutputFormat)
            raise typer.BadParameter(
                f"Invalid output format '{val}'. Choose from: {valid}"
            ) from exc
    return formats


TRUE_SET = {"1", "true", "yes"}


def resolve_bool(
    ctx: typer.Context,
    name: str,
    value: bool,
    cfg: Mapping[str, str],
    key: str,
) -> bool:
    """Return boolean from config if option not explicitly provided."""
    if ctx.get_parameter_source(name) is ParameterSource.DEFAULT:
        val = cfg.get(key)
        if isinstance(val, str):
            return val.lower() in TRUE_SET
        if isinstance(val, bool):
            return val
    return value


def resolve_int(
    ctx: typer.Context,
    name: str,
    value: int,
    cfg: Mapping[str, str],
    key: str,
) -> int:
    """Return integer from config if option not explicitly provided."""
    if ctx.get_parameter_source(name) is ParameterSource.DEFAULT:
        val = cfg.get(key)
        if val is not None:
            try:
                return int(val)
            except ValueError:
                return value
    return value


def resolve_str(
    ctx: typer.Context,
    name: str,
    value: T | None,
    cfg: Mapping[str, str],
    key: str,
) -> T | None:
    """Return string from config if option not explicitly provided."""
    if ctx.get_parameter_source(name) is ParameterSource.DEFAULT:
        return cfg.get(key, value)  # type: ignore[return-value]
    return value


DEFAULT_ENV_VARS: dict[str, str | None] = {
    "DOCS_SITE_URL": "https://alangunning.github.io",
    "DOCS_BASE_URL": "/doc-ai-analysis-starter/docs/",
    "GITHUB_ORG": "alangunning",
    "GITHUB_REPO": "doc-ai-analysis-starter",
    "PR_REVIEW_MODEL": "gpt-4.1",
    "MODEL_PRICE_GPT_4O_INPUT": "0.005",
    "MODEL_PRICE_GPT_4O_OUTPUT": "0.015",
    "OUTPUT_FORMATS": "markdown,html,json,text,doctags",
    "DISABLE_ALL_WORKFLOWS": "false",
    "ENABLE_CONVERT_WORKFLOW": "true",
    "ENABLE_VALIDATE_WORKFLOW": "true",
    "ENABLE_VECTOR_WORKFLOW": "true",
    "ENABLE_PROMPT_ANALYSIS_WORKFLOW": "true",
    "ENABLE_PR_REVIEW_WORKFLOW": "true",
    "ENABLE_DOCS_WORKFLOW": "true",
    "ENABLE_LINT_WORKFLOW": "true",
    "ENABLE_AUTO_MERGE_WORKFLOW": "false",
}


@functools.lru_cache()
def load_env_defaults() -> dict[str, str | None]:
    """Load default settings from the repository's .env.example file.

    If the example file is not present (e.g. when installed from a wheel),
    return a built-in set of defaults so ``config show`` can still display
    available configuration options.
    """
    example_path = Path(__file__).resolve().parents[2] / ".env.example"
    if example_path.exists():
        return dotenv_values(example_path)  # type: ignore[return-value]
    return dict(DEFAULT_ENV_VARS)


def validate_doc(
    raw: Path,
    rendered: Path,
    fmt: OutputFormat | None = None,
    prompt: Path | None = None,
    model: str | None = None,
    base_url: str | None = None,
    show_progress: bool = False,
    logger: logging.Logger | None = None,
    console: Console | None = None,
    validate_file_func: Callable | None = None,
    *,
    force: bool = False,
) -> None:
    """Validate a converted document against its raw source."""
    if validate_file_func is None:
        from doc_ai.cli import validate_file as validate_file_func  # type: ignore

    meta = load_metadata(raw)
    file_hash = compute_hash(raw)
    if not force and meta.blake2b == file_hash and is_step_done(meta, "validation"):
        return
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}
    if fmt is None:
        fmt = EXTENSION_MAP.get(rendered.suffix)
        if fmt is None:
            valid = ", ".join(EXTENSION_MAP.keys())
            raise typer.BadParameter(
                f"Unknown file extension '{rendered.suffix}'. Expected one of: {valid}"
            )
    prompt_path = prompt
    if prompt_path is None:
        doc_prompt = raw.with_name(f"{raw.stem}.validate.prompt.yaml")
        dir_prompt = raw.with_name("validate.prompt.yaml")
        if doc_prompt.exists():
            prompt_path = doc_prompt
        elif dir_prompt.exists():
            prompt_path = dir_prompt
        else:
            repo_root = Path(__file__).resolve().parents[2]
            prompt_path = repo_root / ".github/prompts/validate-output.validate.prompt.yaml"
    verdict = validate_file_func(
        raw,
        rendered,
        fmt,
        prompt_path,
        model=model,
        base_url=base_url,
        show_progress=show_progress,
        logger=logger,
        console=console,
    )
    match = verdict.get("match", False)
    now = datetime.now(timezone.utc).isoformat()
    meta.date_modified = now
    mark_step(
        meta,
        "validation",
        done=match,
        outputs=[rendered.name],
        inputs={
            "prompt": prompt_path.name,
            "rendered": rendered.name,
            "rendered_blake2b": compute_hash(rendered),
            "format": fmt.value,
            "model": model,
            "base_url": base_url,
            "document": str(raw),
            "validated_at": now,
            "verdict": verdict,
        },
    )
    save_metadata(raw, meta)
    if not match:
        raise click.ClickException(f"Mismatch detected: {verdict}")


def analyze_doc(
    markdown_doc: Path,
    prompt: Path | None = None,
    output: Path | None = None,
    model: str | None = None,
    base_url: str | None = None,
    require_json: bool = False,
    show_cost: bool = False,
    estimate: bool = True,
    run_prompt_func: Callable | None = None,
    *,
    force: bool = False,
) -> None:
    """Run an analysis prompt on a markdown document and store results."""
    if run_prompt_func is None:
        from doc_ai.cli import run_prompt as run_prompt_func  # type: ignore

    step_name = "analysis"
    raw_doc = markdown_doc
    if ".converted" in markdown_doc.suffixes:
        raw_doc = raw_doc.with_suffix("").with_suffix("")
    meta = load_metadata(raw_doc)
    md_hash = compute_hash(markdown_doc)
    prev_hash = None
    if meta.extra:
        prev_hash = (
            meta.extra.get("inputs", {})
            .get(step_name, {})
            .get("markdown_blake2b")
        )
    if not force and is_step_done(meta, step_name) and prev_hash == md_hash:
        return

    prompt_path = prompt
    if prompt_path is None:
        type_prompt = markdown_doc.parent / (
            f"{markdown_doc.parent.name}.analysis.prompt.yaml"
        )
        dir_prompt = markdown_doc.parent / "analysis.prompt.yaml"
        if type_prompt.exists():
            prompt_path = type_prompt
        elif dir_prompt.exists():
            prompt_path = dir_prompt
        else:
            repo_root = Path(__file__).resolve().parents[2]
            prompt_path = repo_root / ".github/prompts/doc-analysis.analysis.prompt.yaml"

    result, _ = run_prompt_func(
        prompt_path,
        markdown_doc.read_text(),
        model=model,
        base_url=base_url,
        show_cost=show_cost,
        estimate=estimate,
    )
    result = result.strip()
    fence = re.match(r"```(?:json)?\n([\s\S]*?)\n```", result)
    if fence:
        result = fence.group(1).strip()
    parsed: dict | list | None = None
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        if require_json:
            raise ValueError("Analysis result is not valid JSON")
    if output:
        out_path = output
    else:
        base = markdown_doc
        if base.suffix == ".md":
            base = base.with_suffix("")
        if base.suffix == ".converted":
            base = base.with_suffix("")
        suffix = ".analysis.json" if parsed is not None else ".analysis.txt"
        out_path = base.with_name(f"{base.name}{suffix}")
    if parsed is not None:
        out_path.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
    else:
        out_path.write_text(result + "\n", encoding="utf-8")
    logger.info(
        "[green]Analyzed %s -> %s (SUCCESS)[/]",
        markdown_doc,
        out_path,
    )
    mark_step(
        meta,
        step_name,
        outputs=[out_path.name],
        inputs={
            "prompt": prompt_path.name,
            "markdown": markdown_doc.name,
            "markdown_blake2b": md_hash,
        },
    )
    save_metadata(raw_doc, meta)
