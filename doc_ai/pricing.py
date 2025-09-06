"""Token pricing utilities."""

from __future__ import annotations

import os
from typing import Dict


def get_model_prices() -> Dict[str, Dict[str, float]]:
    """Return per-token pricing for configured models.

    Environment variables of the form ``MODEL_PRICE_<MODEL>_INPUT`` and
    ``MODEL_PRICE_<MODEL>_OUTPUT`` (representing USD cost per 1K tokens) are
    loaded and converted into a mapping of model name to input/output prices.
    The model portion of the variable name is converted to lowercase with
    hyphens. For example ``MODEL_PRICE_GPT_4O_INPUT`` maps to ``gpt-4o``.
    """
    prices: Dict[str, Dict[str, float]] = {}
    prefix = "MODEL_PRICE_"
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        rest = key[len(prefix) :]
        if rest.endswith("_INPUT"):
            model_key = rest[: -len("_INPUT")]
            field = "input"
        elif rest.endswith("_OUTPUT"):
            model_key = rest[: -len("_OUTPUT")]
            field = "output"
        else:
            continue
        model_name = model_key.lower().replace("_", "-")
        try:
            rate = float(value)
        except ValueError:
            continue
        prices.setdefault(model_name, {})[field] = rate
    return prices


def estimate_tokens(text: str, model: str) -> int:
    """Estimate token usage for ``text`` with ``model``.

    Uses ``tiktoken`` if available; otherwise falls back to ``len(text) // 4``.
    """
    try:
        import tiktoken

        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def estimate_cost(
    model: str,
    prompt_tokens: int,
    input_tokens: int,
    output_tokens: int = 0,
) -> float:
    """Estimate USD cost for given token counts and ``model``.

    Rates are interpreted as per-1K token prices. ``prompt_tokens`` and
    ``input_tokens`` are summed before applying the model's input token rate.
    Missing pricing information yields a cost of ``0.0``.
    """
    prices = get_model_prices().get(model.lower(), {})
    input_rate = prices.get("input", 0.0)
    output_rate = prices.get("output", 0.0)
    total_input = prompt_tokens + input_tokens
    return (total_input / 1000) * input_rate + (output_tokens / 1000) * output_rate


__all__ = ["get_model_prices", "estimate_tokens", "estimate_cost"]
