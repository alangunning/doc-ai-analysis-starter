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
    if not isinstance(spec, dict):
        raise ValueError("Prompt file must be a mapping")
    if "model" not in spec or "messages" not in spec:
        raise ValueError("Prompt file must contain 'model' and 'messages'")
    if not isinstance(spec["messages"], list):
        raise ValueError("'messages' must be a list")

    messages = []
    for m in spec["messages"]:
        if not isinstance(m, dict) or "role" not in m or "content" not in m:
            raise ValueError("Each message must contain 'role' and 'content'")
        content = m["content"]
        if m["role"] == "user":
            content = content + "\n\n" + input_text
        messages.append(
            {
                "role": m["role"],
                "content": [{"type": "input_text", "text": content}],
            }
        )

    base = (
        base_url
        or os.getenv("BASE_MODEL_URL")
        or DEFAULT_MODEL_BASE_URL
    )
    api_key_var = "OPENAI_API_KEY" if "api.openai.com" in base else "GITHUB_TOKEN"
    api_key = os.getenv(api_key_var)
    if not api_key:
        raise RuntimeError(f"Missing required environment variable: {api_key_var}")
    client = OpenAI(api_key=api_key, base_url=base)
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
