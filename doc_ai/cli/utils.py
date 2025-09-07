# mypy: ignore-errors
"""Shared utilities for doc_ai CLI."""
from __future__ import annotations

import functools
import logging
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Mapping, Sequence, TypeVar

import questionary
import typer
from click.core import ParameterSource
from dotenv import dotenv_values

try:
    QuestionaryError = questionary.QuestionaryError  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover - older questionary releases
    QuestionaryError = questionary.ValidationError  # type: ignore[assignment]

from doc_ai.converter import OutputFormat, suffix_for_format
from doc_ai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)

if TYPE_CHECKING:  # pragma: no cover - used for type checkers only
    from rich.console import Console

logger = logging.getLogger(__name__)


def discover_doc_types_topics():
    from .interactive import discover_doc_types_topics as _discover

    return _discover()


def discover_topics(doc_type: str):
    from .interactive import discover_topics as _discover

    return _discover(doc_type)


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------


def get_logging_options(ctx: typer.Context) -> tuple[bool, str | None, Path | None]:
    """Return logging options stored on the Typer context.

    The root ``doc-ai`` callback records ``verbose``, ``log_level`` and
    ``log_file`` values on ``ctx.obj`` after configuring logging. Subcommands
    can call this helper to read those options without coupling to the exact
    keys used in the context object.
    """

    obj = ctx.ensure_object(dict)
    verbose = bool(obj.get("verbose", False))
    level = obj.get("log_level")
    log_file = obj.get("log_file")
    return verbose, level, log_file


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


NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def sanitize_name(value: str) -> str:
    """Validate *value* only contains safe characters.

    The CLI uses this to ensure names cannot include characters that might
    lead to path traversal or other unexpected behaviour. Only letters,
    numbers, underscores and hyphens are permitted.
    """

    if not NAME_RE.fullmatch(value):
        raise typer.BadParameter(
            "Invalid name. Use only letters, numbers, underscores and hyphens."
        )
    return value


def prompt_if_missing(
    ctx: typer.Context, value: str | None, message: str
) -> str | None:
    """Return *value* or interactively prompt for it when ``None``.

    The prompt is only shown when the CLI is running in an interactive
    environment (``stdin`` is a TTY and ``ctx.obj['interactive']`` is truthy).
    Any errors from ``questionary`` are suppressed so non-interactive
    sessions fall back gracefully.
    """

    if value is not None:
        return value
    try:
        interactive = bool(ctx.obj.get("interactive", True)) and sys.stdin.isatty()
    except (OSError, AttributeError):
        interactive = False
    if not interactive:
        return value
    try:
        answer = questionary.text(message).ask()
    except QuestionaryError as exc:  # pragma: no cover - best effort
        logger.warning("Prompt failed: %s", exc)
        return value
    return answer or value


def prompt_choice(message: str, choices: Sequence[str]):
    """Return a questionary prompt for *choices* with fuzzy matching.

    Uses :func:`questionary.autocomplete` when available to provide fuzzy
    matching of *choices*.  If ``autocomplete`` is not available or fails,
    fall back to :func:`questionary.select` for a basic list prompt.
    """

    autocomplete = getattr(questionary, "autocomplete", None)
    if autocomplete is not None:
        try:
            return autocomplete(
                message, choices=choices, validate=lambda val: val in choices
            )
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("Autocomplete unavailable: %s", exc)
    return questionary.select(message, choices=choices)


def select_doc_type(ctx: typer.Context, doc_type: str | None) -> str:
    """Return a sanitized document type, prompting when necessary."""
    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    doc_type = doc_type or cfg.get("default_doc_type")
    if doc_type is None:
        doc_types, _ = discover_doc_types_topics()
        if doc_types:
            try:
                doc_type = prompt_choice("Select document type", doc_types).ask()
            except QuestionaryError as exc:
                logger.warning("Failed to select document type: %s", exc)
                doc_type = None
        doc_type = prompt_if_missing(ctx, doc_type, "Document type")
    if doc_type is None:
        raise typer.BadParameter("Document type required")
    return sanitize_name(doc_type)


def select_topic(ctx: typer.Context, doc_type: str, topic: str | None) -> str:
    """Return a sanitized topic for *doc_type*, prompting when necessary."""
    topics = discover_topics(doc_type)
    cfg = ctx.obj.get("config", {}) if ctx.obj else {}
    topic = topic or cfg.get("default_topic")
    if topic is None:
        if topics:
            try:
                topic = prompt_choice("Select topic", topics).ask()
            except QuestionaryError as exc:
                logger.warning("Failed to select topic: %s", exc)
                topic = None
        topic = prompt_if_missing(ctx, topic, "Topic")
    if topic is None:
        raise typer.BadParameter("Topic required")
    return sanitize_name(topic)


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
    "DOC_AI_ALLOW_SHELL": "false",
    "DOC_AI_HISTORY_FILE": "",
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
    from datetime import datetime, timezone

    import click

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
            prompt_path = (
                repo_root / ".github/prompts/validate-output.validate.prompt.yaml"
            )
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
    topic: str | None = None,
    run_prompt_func: Callable | None = None,
    *,
    force: bool = False,
) -> None:
    """Run an analysis prompt on a markdown document and store results."""
    import json
    import re

    if run_prompt_func is None:
        from doc_ai.cli import run_prompt as run_prompt_func  # type: ignore

    step_name = "analysis" if topic is None else f"analysis:{topic}"
    raw_doc = markdown_doc
    if ".converted" in markdown_doc.suffixes:
        raw_doc = raw_doc.with_suffix("").with_suffix("")
    meta = load_metadata(raw_doc)
    md_hash = compute_hash(markdown_doc)
    prev_hash = None
    if meta.extra:
        prev_hash = (
            meta.extra.get("inputs", {}).get(step_name, {}).get("markdown_blake2b")
        )
    if not force and is_step_done(meta, step_name) and prev_hash == md_hash:
        return

    prompt_path = prompt
    if prompt_path is None:
        parent = markdown_doc.parent
        if topic:
            type_prompt = parent / f"{parent.name}.analysis.{topic}.prompt.yaml"
            topic_prompt = parent / f"analysis_{topic}.prompt.yaml"
            if type_prompt.exists():
                prompt_path = type_prompt
            elif topic_prompt.exists():
                prompt_path = topic_prompt
            else:
                repo_root = Path(__file__).resolve().parents[2]
                alt1 = (
                    repo_root
                    / f".github/prompts/doc-analysis.analysis.{topic}.prompt.yaml"
                )
                alt2 = (
                    repo_root
                    / f".github/prompts/doc-analysis.analysis_{topic}.prompt.yaml"
                )
                if alt1.exists():
                    prompt_path = alt1
                elif alt2.exists():
                    prompt_path = alt2
                else:
                    prompt_path = (
                        repo_root / ".github/prompts/doc-analysis.analysis.prompt.yaml"
                    )
        else:
            type_prompt = parent / f"{parent.name}.analysis.prompt.yaml"
            dir_prompt = parent / "analysis.prompt.yaml"
            if type_prompt.exists():
                prompt_path = type_prompt
            elif dir_prompt.exists():
                prompt_path = dir_prompt
            else:
                repo_root = Path(__file__).resolve().parents[2]
                prompt_path = (
                    repo_root / ".github/prompts/doc-analysis.analysis.prompt.yaml"
                )

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
        topic_part = f".{topic}" if topic else ""
        suffix = (
            f".analysis{topic_part}.json"
            if parsed is not None
            else f".analysis{topic_part}.txt"
        )
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
            "topic": topic,
        },
    )
    save_metadata(raw_doc, meta)
