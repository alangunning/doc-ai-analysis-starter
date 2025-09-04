"""Prompt execution helpers."""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple

import yaml
from openai import OpenAI

from doc_ai.pricing import estimate_cost, estimate_tokens

logger = logging.getLogger(__name__)

DEFAULT_MODEL_BASE_URL = "https://models.github.ai/inference"


def run_prompt(
    prompt_file: Path,
    input_text: str,
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    show_cost: bool = False,
    estimate: bool = True,
) -> Tuple[str, float]:
    """Execute ``prompt_file`` against ``input_text`` and return model output.

    Returns a tuple of ``(output_text, actual_cost)`` where cost is in USD.
    When ``show_cost`` is true, a pre-run estimate is displayed unless
    ``estimate`` is false.
    """
    spec = yaml.safe_load(prompt_file.read_text())
    if not isinstance(spec, dict):
        raise ValueError("Prompt file must be a mapping")
    if "model" not in spec or "messages" not in spec:
        raise ValueError("Prompt file must contain 'model' and 'messages'")
    if not isinstance(spec["messages"], list):
        raise ValueError("'messages' must be a list")

    messages = []
    prompt_tokens = 0
    model_name = model or spec["model"]
    for m in spec["messages"]:
        if not isinstance(m, dict) or "role" not in m or "content" not in m:
            raise ValueError("Each message must contain 'role' and 'content'")
        content = m["content"]
        prompt_tokens += estimate_tokens(content, model_name)
        if m["role"] == "user":
            content = content + "\n\n" + input_text
        messages.append(
            {
                "role": m["role"],
                "content": [{"type": "input_text", "text": content}],
            }
        )

    user_tokens = estimate_tokens(input_text, model_name)
    if show_cost and estimate:
        est = estimate_cost(model_name, prompt_tokens, user_tokens)
        logger.info(
            "Estimated cost: $%.6f (%d input tokens)",
            est,
            prompt_tokens + user_tokens,
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
        model=model_name,
        input=messages,
        **params,
    )
    input_tokens = getattr(getattr(response, "usage", {}), "input_tokens", 0)
    output_tokens = getattr(getattr(response, "usage", {}), "output_tokens", 0)
    actual_cost = estimate_cost(model_name, 0, input_tokens, output_tokens)
    if show_cost:
        logger.info(
            "Actual cost: $%.6f (%d in, %d out tokens)",
            actual_cost,
            input_tokens,
            output_tokens,
        )
    return response.output_text, actual_cost


__all__ = ["run_prompt", "DEFAULT_MODEL_BASE_URL"]
