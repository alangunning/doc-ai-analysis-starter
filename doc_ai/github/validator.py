"""Rendering validation helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict
import tempfile
import contextlib

import yaml
from dotenv import load_dotenv
from openai import OpenAI
from rich.progress import Progress

from ..converter import OutputFormat
from ..openai import input_file_from_path, input_file_from_url
from .prompts import DEFAULT_MODEL_BASE_URL

OPENAI_BASE_URL = "https://api.openai.com/v1"

load_dotenv()


def _build_input(
    client: OpenAI,
    raw_path: Path,
    rendered_path: Path,
    fmt: OutputFormat,
    prompt_path: Path,
    *,
    use_upload: bool = False,
    url_only: bool = False,
    url_base: str | None = None,
    progress: Progress | None = None,
    task: int | None = None,
) -> Dict:
    """Build response ``input`` attaching raw and rendered documents."""
    spec = yaml.safe_load(prompt_path.read_text())
    input_msgs = [dict(m) for m in spec["messages"]]

    def _github_url(path: Path) -> str:
        if url_base:
            return f"{url_base}/{path.name}"
        repo = os.getenv("GITHUB_REPOSITORY")
        ref = os.getenv("GITHUB_SHA", "main")
        try:
            rel = path.resolve().relative_to(Path.cwd()).as_posix()
        except ValueError:
            rel = path.name
        return f"https://raw.githubusercontent.com/{repo}/{ref}/{rel}"

    def _payload(path: Path):
        if url_only:
            return input_file_from_url(_github_url(path))
        if path.suffix.lower() == ".pdf":
            payload = input_file_from_path(
                client, path, purpose="assistants", use_upload=use_upload
            )
        else:
            with path.open("rb") as src, tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
                tmp.write(src.read())
                tmp.flush()
                tmp.seek(0)
                payload = input_file_from_path(
                    client, tmp.name, purpose="assistants", use_upload=use_upload
                )
        if progress and task is not None:
            progress.advance(task)
        return payload

    raw_payload = _payload(raw_path)
    rendered_payload = _payload(rendered_path)

    for msg in input_msgs:
        if msg.get("role") == "user":
            text = msg.get("content", "").replace("{format}", fmt.value)
            msg["content"] = [
                {"type": "input_text", "text": text},
                raw_payload,
                rendered_payload,
            ]
            break
    return spec, input_msgs


def validate_file(
    raw_path: Path,
    rendered_path: Path,
    fmt: OutputFormat,
    prompt_path: Path,
    model: str | None = None,
    base_url: str | None = None,
    show_progress: bool = False,
) -> Dict:
    """Validate ``rendered_path`` against ``raw_path`` for ``fmt``.

    Depending on the ``VALIDATE_FILE_MODE`` environment variable the raw and
    rendered files are either uploaded via the ``/v1/files`` endpoint
    (``files``), streamed through the resumable ``/v1/uploads`` API
    (``uploads``) or referenced directly by their GitHub ``raw`` URLs
    (``url``). The resulting file inputs are then attached to a
    :meth:`client.responses.create` call. This approach avoids token overflows
    on large documents and works with models that support file inputs. GitHub
    Models do not offer file uploads, so when the base URL points at the GitHub
    provider (or is unspecified) the call is automatically routed to
    ``https://api.openai.com/v1`` using the ``OPENAI_API_KEY`` token. Returns the
    model's JSON verdict as a dictionary.
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
    file_mode = os.getenv("VALIDATE_FILE_MODE", "files").lower()
    use_upload = file_mode == "uploads"
    url_only = file_mode == "url"
    url_base = os.getenv("VALIDATE_FILE_URL_BASE")
    total = 0 if url_only else 2
    cm = Progress() if show_progress else contextlib.nullcontext()
    with cm as progress:
        upload_task = (
            progress.add_task("Uploading files", total=total) if show_progress else None
        )
        spec, input_msgs = _build_input(
            client,
            raw_path,
            rendered_path,
            fmt,
            prompt_path,
            use_upload=use_upload,
            url_only=url_only,
            url_base=url_base,
            progress=progress if show_progress else None,
            task=upload_task,
        )
        request_task = (
            progress.add_task("Requesting validation", total=1) if show_progress else None
        )
        result = client.responses.create(
            model=model or spec["model"],
            input=input_msgs,
            **spec.get("modelParameters", {}),
        )
        if show_progress and request_task is not None:
            progress.advance(request_task)
    text = result.output_text or "{}"
    return json.loads(text)


__all__ = ["validate_file"]
