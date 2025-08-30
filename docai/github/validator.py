"""Rendering validation helpers."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Dict

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from ..converter import OutputFormat

load_dotenv()


def _build_messages(raw_bytes: bytes, rendered_text: str, fmt: OutputFormat, prompt_path: Path) -> Dict:
    spec = yaml.safe_load(prompt_path.read_text())
    messages = [dict(m) for m in spec["messages"]]
    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            text = msg.get("content", "").format(format=fmt.value)
            messages[i]["content"] = [
                {"type": "input_text", "text": text},
                {"type": "document", "format": "pdf", "b64_content": base64.b64encode(raw_bytes).decode()},
                {"type": "text", "text": rendered_text},
            ]
            break
    return spec, messages


def validate_file(
    raw_path: Path,
    rendered_path: Path,
    fmt: OutputFormat,
    prompt_path: Path,
) -> Dict:
    """Validate ``rendered_path`` against ``raw_path`` for ``fmt``.

    Returns the model's JSON verdict as a dictionary.
    """

    spec, messages = _build_messages(
        raw_path.read_bytes(), rendered_path.read_text(), fmt, prompt_path
    )
    client = OpenAI(
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.github.ai",
    )
    result = client.responses.create(
        model=spec["model"],
        **spec.get("modelParameters", {}),
        input=messages,
    )
    text = result.output[0].content[0].get("text", "{}")
    return json.loads(text)


__all__ = ["validate_file"]
