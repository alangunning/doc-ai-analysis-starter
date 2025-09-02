"""Rendering validation helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

import requests
import yaml
from dotenv import load_dotenv
from openai import OpenAI

from ..converter import OutputFormat
from ..openai import create_response
from rich.progress import Progress
from .prompts import DEFAULT_MODEL_BASE_URL

OPENAI_BASE_URL = "https://api.openai.com/v1"

load_dotenv()


def validate_file(
    raw_path: Path | str,
    rendered_path: Path | str,
    fmt: OutputFormat,
    prompt_path: Path,
    model: str | None = None,
    base_url: str | None = None,
    show_progress: bool = False,
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
    client = OpenAI(api_key=os.getenv(api_key_var), base_url=base)

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
            s = str(p)
            if s.lower().endswith(".pdf"):
                file_urls.append(s)
            else:
                resp = requests.get(s)
                resp.raise_for_status()
                texts.append(resp.text)
        else:
            path = Path(p)
            if path.suffix.lower() == ".pdf":
                file_paths.append(path)
            else:
                texts.append(path.read_text(encoding="utf-8"))

    progress_cb: Optional[Callable[[int], None]] = None
    progress: Optional[Progress] = None
    upload_task = validate_task = None
    if show_progress:
        progress = Progress()
        progress.start()
        if file_paths:
            total = sum(p.stat().st_size for p in file_paths)
            upload_task = progress.add_task("Uploading", total=total)

            def progress_cb(n: int) -> None:  # pragma: no cover - callback
                progress.advance(upload_task, n)
        validate_task = progress.add_task("Validating", total=100)

    try:
        if progress and validate_task is not None:
            progress.advance(validate_task, 5)
        result = create_response(
            client,
            model=model or spec["model"],
            system=system_msgs,
            texts=texts,
            file_urls=file_urls or None,
            file_paths=file_paths or None,
            progress=progress_cb,
            **spec.get("modelParameters", {}),
        )
        if progress and validate_task is not None:
            progress.update(validate_task, completed=100)
    finally:
        if progress is not None:
            progress.stop()

    text = (result.output_text or "").strip()
    if not text:
        raise ValueError("Model response contained no text")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model response was not valid JSON: {text}") from exc


__all__ = ["validate_file"]
