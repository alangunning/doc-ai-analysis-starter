"""Rendering validation helpers."""

from __future__ import annotations

import base64
import json
import os
import mimetypes
from pathlib import Path
from typing import Dict

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from ..converter import OutputFormat
from .prompts import DEFAULT_MODEL_BASE_URL

load_dotenv()


def _build_messages(raw_path: Path, rendered_text: str, fmt: OutputFormat, prompt_path: Path) -> Dict:
    """Build OpenAI chat messages embedding the raw file and rendered text."""
    spec = yaml.safe_load(prompt_path.read_text())
    messages = [dict(m) for m in spec["messages"]]
    raw_bytes = raw_path.read_bytes()
    raw_b64 = base64.b64encode(raw_bytes).decode()
    mime_type, _ = mimetypes.guess_type(raw_path)
    mime_type = mime_type or "application/octet-stream"
    raw_data_url = f"data:{mime_type};base64,{raw_b64}"
    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            text = msg.get("content", "").replace("{format}", fmt.value)
            messages[i]["content"] = [
                {"type": "text", "text": text},
                {
                    "type": "file",
                    "file": {"file_data": raw_data_url, "filename": raw_path.name},
                },
                {"type": "text", "text": rendered_text},
            ]
            break
    return spec, messages


def validate_file(
    raw_path: Path,
    rendered_path: Path,
    fmt: OutputFormat,
    prompt_path: Path,
    model: str | None = None,
    base_url: str | None = None,
) -> Dict:
    """Validate ``rendered_path`` against ``raw_path`` for ``fmt``.

    Returns the model's JSON verdict as a dictionary.
    """

    spec, messages = _build_messages(raw_path, rendered_path.read_text(), fmt, prompt_path)
    client = OpenAI(
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url=base_url
        or os.getenv("VALIDATE_BASE_MODEL_URL")
        or os.getenv("BASE_MODEL_URL")
        or DEFAULT_MODEL_BASE_URL,
    )
    result = client.chat.completions.create(
        model=model or spec["model"],
        messages=messages,
        **spec.get("modelParameters", {}),
    )
    text = result.choices[0].message.content or "{}"
    return json.loads(text)


__all__ = ["validate_file"]
