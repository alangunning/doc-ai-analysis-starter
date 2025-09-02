from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List

from rich.console import Console

from doc_ai.converter import OutputFormat, suffix_for_format
from doc_ai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)

ASCII_ART = r"""
 ____   ___   ____      _    ___    ____ _     ___
|  _ \ / _ \ / ___|    / \  |_ _|  / ___| |   |_ _|
| | | | | | | |       / _ \  | |  | |   | |    | |
| |_| | |_| | |___   / ___ \ | |  | |___| |___ | |
|____/ \___/ \____| /_/   \_\___|  \____|_____|___|
"""


def print_banner() -> None:  # pragma: no cover - visual flair only
    from doc_ai.cli import console as global_console  # type: ignore
    global_console.print(f"[bold green]{ASCII_ART}[/bold green]")


def converted_suffix(fmt: OutputFormat) -> str:
    return f".converted{suffix_for_format(fmt)}"


def infer_format(path: Path) -> OutputFormat:
    mapping = {
        ".md": OutputFormat.MARKDOWN,
        ".html": OutputFormat.HTML,
        ".json": OutputFormat.JSON,
        ".txt": OutputFormat.TEXT,
        ".doctags": OutputFormat.DOCTAGS,
        ".dogtags": OutputFormat.DOCTAGS,
    }
    try:
        return mapping[path.suffix.lower()]
    except KeyError as exc:  # pragma: no cover - user error
        valid = ", ".join(mapping.keys())
        raise ValueError(f"Unknown file extension '{path.suffix}'. Expected one of: {valid}") from exc


def parse_env_formats() -> List[OutputFormat] | None:
    env_val = os.getenv("OUTPUT_FORMATS")
    if not env_val:
        return None
    formats: List[OutputFormat] = []
    for val in env_val.split(","):
        formats.append(OutputFormat(val.strip()))
    return formats


def validate_doc(
    raw: Path,
    rendered: Path,
    fmt: OutputFormat | None = None,
    prompt: Path | None = None,
    model: str | None = None,
    base_url: str | None = None,
    show_progress: bool = False,
    logger=None,
    console_obj: Console | None = None,
) -> None:
    meta = load_metadata(raw)
    file_hash = compute_hash(raw)
    if meta.blake2b == file_hash and is_step_done(meta, "validation"):
        return
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}
    if fmt is None:
        fmt = infer_format(rendered)
    prompt_path = prompt
    if prompt_path is None:
        doc_prompt = raw.with_name(f"{raw.stem}.validate.prompt.yaml")
        dir_prompt = raw.with_name("validate.prompt.yaml")
        if doc_prompt.exists():
            prompt_path = doc_prompt
        elif dir_prompt.exists():
            prompt_path = dir_prompt
        else:
            prompt_path = Path(".github/prompts/validate-output.validate.prompt.yaml")
    from doc_ai.cli import validate_file  # type: ignore
    verdict = validate_file(
        raw,
        rendered,
        fmt,
        prompt_path,
        model=model,
        base_url=base_url,
        show_progress=show_progress,
        logger=logger,
        console=console_obj,
    )
    if not verdict.get("match", False):
        raise RuntimeError(f"Mismatch detected: {verdict}")
    mark_step(
        meta,
        "validation",
        outputs=[rendered.name],
        inputs={
            "prompt": prompt_path.name,
            "rendered": rendered.name,
            "format": fmt.value,
        },
    )
    save_metadata(raw, meta)


def analyze_doc(
    markdown_doc: Path,
    prompt: Path | None = None,
    output: Path | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> None:
    step_name = "analysis"
    raw_doc = markdown_doc
    if ".converted" in markdown_doc.suffixes:
        raw_doc = raw_doc.with_suffix("").with_suffix("")
    meta = load_metadata(raw_doc)
    md_hash = compute_hash(markdown_doc)
    prev_hash = None
    if meta.extra:
        prev_hash = meta.extra.get("inputs", {}).get(step_name, {}).get("markdown_blake2b")
    if is_step_done(meta, step_name) and prev_hash == md_hash:
        return
    prompt_path = prompt
    if prompt_path is None:
        type_prompt = markdown_doc.parent / f"{markdown_doc.parent.name}.analysis.prompt.yaml"
        dir_prompt = markdown_doc.parent / "analysis.prompt.yaml"
        if type_prompt.exists():
            prompt_path = type_prompt
        elif dir_prompt.exists():
            prompt_path = dir_prompt
        else:
            prompt_path = Path(".github/prompts/doc-analysis.analysis.prompt.yaml")
    from doc_ai.cli import run_prompt  # type: ignore
    result = run_prompt(
        prompt_path,
        markdown_doc.read_text(),
        model=model,
        base_url=base_url,
    )
    result = result.strip()
    fence = re.match(r"```(?:json)?\n([\s\S]*?)\n```", result)
    if fence:
        result = fence.group(1).strip()
    if output:
        out_path = output
    else:
        base = markdown_doc
        if base.suffix == ".md":
            base = base.with_suffix("")
        if base.suffix == ".converted":
            base = base.with_suffix("")
        out_path = base.with_name(f"{base.name}.analysis.json")
    out_path.write_text(result + "\n", encoding="utf-8")
    from doc_ai.cli import console as global_console  # type: ignore
    global_console.print(f"[green]Analyzed {markdown_doc} -> {out_path} (SUCCESS)[/]")
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


__all__ = [
    "print_banner",
    "converted_suffix",
    "infer_format",
    "parse_env_formats",
    "validate_doc",
    "analyze_doc",
]
