"""Prompt execution helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def run_prompt(prompt_file: Path, input_text: str, *, model: Optional[str] = None) -> str:
    """Execute ``prompt_file`` against ``input_text`` and return model output."""

    spec = yaml.safe_load(prompt_file.read_text())
    messages = [dict(m) for m in spec["messages"]]
    for msg in reversed(messages):
        if msg.get("role") == "user":
            msg["content"] = msg.get("content", "") + "\n\n" + input_text
            break
    client = OpenAI(
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.github.ai",
    )
    response = client.responses.create(
        model=model or spec["model"],
        **spec.get("modelParameters", {}),
        input=messages,
    )
    return response.output[0].content[0].get("text", "")


__all__ = ["run_prompt"]
