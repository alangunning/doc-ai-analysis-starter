"""Rendering validation helpers."""

from __future__ import annotations

import json
import re
import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

import yaml
from openai import OpenAI

from ..converter import OutputFormat
from ..openai import create_response, upload_file
from ..utils import http_get, sanitize_path
from rich.console import Console
from rich.progress import Progress
from .prompts import DEFAULT_MODEL_BASE_URL

OPENAI_BASE_URL = "https://api.openai.com/v1"


def validate_file(
    raw_path: Path | str,
    rendered_path: Path | str,
    fmt: OutputFormat,
    prompt_path: Path,
    model: str | None = None,
    base_url: str | None = None,
    show_progress: bool = False,
    logger: logging.Logger | None = None,
    console: Console | None = None,
) -> Dict:
    """Validate ``rendered_path`` against ``raw_path`` for ``fmt``.

    The raw and rendered files may be local paths or remote URLs. Local files are
    uploaded as needed using the most suitable OpenAI file API; remote URLs are
    passed directly to the Responses API. GitHub Models do not offer file
    uploads, so when the base URL points at the GitHub provider (or is
    unspecified) the call is automatically routed to ``https://api.openai.com/v1``
    using the ``OPENAI_API_KEY`` token. Returns the model's JSON verdict as a
    dictionary.

    Parameters
    ----------
    show_progress:
        When ``True``, emit progress events for file uploads so callers can
        display progress bars.
    logger:
        Optional logger to receive serialized request and response payloads.
    console:
        Optional :class:`rich.console.Console` used for rendering progress bars and
        for rich logging handlers. A new console is created when omitted.
    """

    base = (
        base_url
        or os.getenv("VALIDATE_BASE_MODEL_URL")
        or os.getenv("BASE_MODEL_URL")
        or DEFAULT_MODEL_BASE_URL
    )
    if not base or "models.github.ai" in base:
        base = OPENAI_BASE_URL
    api_key_var = "OPENAI_API_KEY" if "api.openai.com" in base else "GITHUB_TOKEN"
    api_key = os.getenv(api_key_var)
    if not api_key:
        raise RuntimeError(f"Missing required environment variable: {api_key_var}")
    client = OpenAI(api_key=api_key, base_url=base)

    prompt_path = sanitize_path(prompt_path)
    spec = yaml.safe_load(prompt_path.read_text())
    system_msgs = [m["content"] for m in spec["messages"] if m.get("role") == "system"]
    user_msgs: List[str] = [m["content"] for m in spec["messages"] if m.get("role") == "user"]
    user_text = user_msgs[0].replace("{format}", fmt.value) if user_msgs else ""

    def _is_url(value: Path | str) -> bool:
        s = str(value)
        return s.startswith("http://") or s.startswith("https://")

    texts: List[str] = [user_text]
    file_urls: List[str] = []
    file_paths: List[Path] = []
    for p in (raw_path, rendered_path):
        if _is_url(p):
            if str(p).lower().endswith(".pdf"):
                file_urls.append(str(p))
            else:
                resp = http_get(str(p))
                resp.raise_for_status()
                texts.append(resp.text)
        else:
            path = sanitize_path(p)
            if path.suffix.lower() == ".pdf":
                file_paths.append(path)
            else:
                texts.append(path.read_text(encoding="utf-8"))

    progress_cb: Optional[Callable[[int], None]] = None
    progress: Optional[Progress] = None
    upload_task = validate_task = None
    file_ids: List[str] = []
    if show_progress:
        progress = Progress(console=console or Console())
        progress.start()
        if file_paths:
            total = sum(p.stat().st_size for p in file_paths)
            upload_task = progress.add_task("Uploading", total=total)

            def progress_cb(n: int) -> None:  # pragma: no cover - callback
                progress.advance(upload_task, n)

    try:
        if file_paths:
            for path in file_paths:
                file_ids.append(
                    upload_file(
                        client,
                        path,
                        progress=progress_cb,
                        logger=logger,
                    )
                )
        if progress and upload_task is not None:
            progress.update(upload_task, completed=sum(p.stat().st_size for p in file_paths))
            progress.remove_task(upload_task)
        if progress:
            validate_task = progress.add_task("Validating", total=100)
            progress.advance(validate_task, 5)
        result = create_response(
            client,
            model=model or spec["model"],
            system=system_msgs,
            texts=texts,
            file_urls=file_urls or None,
            file_ids=file_ids or None,
            logger=logger,
            **spec.get("modelParameters", {}),
        )
        if progress and validate_task is not None:
            progress.update(validate_task, completed=100)
    finally:
        if progress is not None:
            progress.stop()

    text = (result.output_text or "").strip()
    if logger:
        logger.debug("Validation output_text: %s", text)
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    if not text:
        raise ValueError("Model response contained no text")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model response was not valid JSON: {text}") from exc


__all__ = ["validate_file"]
