"""Prompt execution helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from openai import OpenAI

DEFAULT_MODEL_BASE_URL = "https://models.github.ai/inference"


def run_prompt(
    prompt_file: Path,
    input_text: str,
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    """Execute ``prompt_file`` against ``input_text`` and return model output."""

    spec = yaml.safe_load(prompt_file.read_text())
    messages = []
    for m in spec["messages"]:
        content = m.get("content", "")
        if m.get("role") == "user":
            content = content + "\n\n" + input_text
        messages.append(
            {
                "role": m.get("role", "user"),
                "content": [{"type": "input_text", "text": content}],
            }
        )
    client = OpenAI(
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url=base_url
        or os.getenv("BASE_MODEL_URL")
        or DEFAULT_MODEL_BASE_URL,
    )
    allowed = {
        "temperature",
        "top_p",
        "tools",
        "tool_choice",
        "parallel_tool_calls",
        "metadata",
        "max_output_tokens",
        "text",
    }
    params = {
        k: v for k, v in spec.get("modelParameters", {}).items() if k in allowed
    }
    response = client.responses.create(
        model=model or spec["model"],
        input=messages,
        **params,
    )
    return response.output_text


__all__ = ["run_prompt", "DEFAULT_MODEL_BASE_URL"]
