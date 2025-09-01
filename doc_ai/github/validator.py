"""Rendering validation helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

import yaml
from dotenv import load_dotenv
from openai import OpenAI

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
) -> Dict:
    """Build response ``input`` attaching raw and rendered documents."""
    spec = yaml.safe_load(prompt_path.read_text())
    input_msgs = [dict(m) for m in spec["messages"]]

    # Upload the raw and rendered files so the model can access them without
    # hitting token limits on large documents.
    with raw_path.open("rb") as f:
        raw_file = client.files.create(file=f, purpose="assistants")
    with rendered_path.open("rb") as f:
        rendered_file = client.files.create(file=f, purpose="assistants")

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
    spec, input_msgs = _build_input(client, raw_path, rendered_path, fmt, prompt_path)
    result = client.responses.create(
        model=model or spec["model"],
        input=input_msgs,
        **spec.get("modelParameters", {}),
    )
    text = result.output_text or "{}"
    return json.loads(text)


__all__ = ["validate_file"]
