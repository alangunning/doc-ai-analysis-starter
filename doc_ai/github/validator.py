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
from .prompts import DEFAULT_MODEL_BASE_URL

OPENAI_BASE_URL = "https://api.openai.com/v1"

load_dotenv()


def _build_input(
    client: OpenAI,
    raw_path: Path,
    rendered_path: Path,
    fmt: OutputFormat,
    prompt_path: Path,
    progress: Progress | None = None,
    task: int | None = None,
) -> Dict:
    """Build response ``input`` attaching raw and rendered documents."""
    spec = yaml.safe_load(prompt_path.read_text())
    input_msgs = [dict(m) for m in spec["messages"]]

    # Upload the raw and rendered files so the model can access them without
    # hitting token limits on large documents. The OpenAI file endpoints only
    # accept a limited set of extensions; markdown files for example are not
    # supported. When the rendered document uses an unsupported suffix we upload
    # it as a temporary ``.txt`` file so the request is accepted.

    def _upload(path: Path):
        if path.suffix.lower() == ".pdf":
            with path.open("rb") as f:
                file = client.files.create(file=f, purpose="assistants")
        else:
            with path.open("rb") as src, tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
                tmp.write(src.read())
                tmp.flush()
                tmp.seek(0)
                file = client.files.create(file=tmp, purpose="assistants")
        if progress and task is not None:
            progress.advance(task)
        return file

    raw_file = _upload(raw_path)
    rendered_file = _upload(rendered_path)

    for msg in input_msgs:
        if msg.get("role") == "user":
            text = msg.get("content", "").replace("{format}", fmt.value)
            msg["content"] = [
                {"type": "input_text", "text": text},
                {"type": "input_file", "file_id": raw_file.id},
                {"type": "input_file", "file_id": rendered_file.id},
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

    The files are uploaded via :meth:`client.files.create` and referenced in a
    :meth:`client.responses.create` call using ``input_file`` attachments. This
    approach avoids token overflows on large documents and works with models that
    support file inputs (for example ``gpt-4o`` or the cheaper ``gpt-4o-mini``).
    GitHub Models do not offer file uploads, so when the base URL points at the
    GitHub provider (or is unspecified) the call is automatically routed to
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
    cm = Progress() if show_progress else contextlib.nullcontext()
    with cm as progress:
        upload_task = (
            progress.add_task("Uploading files", total=2) if show_progress else None
        )
        spec, input_msgs = _build_input(
            client,
            raw_path,
            rendered_path,
            fmt,
            prompt_path,
            progress if show_progress else None,
            upload_task,
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
