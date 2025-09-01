"""Convenience helpers for creating Responses API requests."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Sequence, Tuple, Union

from openai import OpenAI

from .files import (
    input_file_from_bytes,
    input_file_from_id,
    input_file_from_url,
)


def input_text(text: str) -> Dict[str, str]:
    """Create an ``input_text`` payload."""

    return {"type": "input_text", "text": text}


def _ensure_seq(value: Union[str, Sequence[str], None]) -> Sequence[str]:
    """Return ``value`` as a sequence."""

    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return value


def create_response(
    client: OpenAI,
    *,
    model: str,
    texts: Union[str, Sequence[str], None] = None,
    file_urls: Union[str, Sequence[str], None] = None,
    file_ids: Union[str, Sequence[str], None] = None,
    file_bytes: Sequence[Tuple[str, bytes]] | None = None,
) -> Any:
    """Call the Responses API with a mix of inputs.

    Parameters
    ----------
    client:
        An :class:`openai.OpenAI` client instance.
    model:
        Target model identifier, e.g. ``"gpt-4.1"``.
    texts:
        One or more user text prompts.
    file_urls:
        One or more URLs of remote files to use as ``input_file`` entries.
    file_ids:
        Identifiers of files previously uploaded to OpenAI.
    file_bytes:
        ``(filename, data)`` tuples for in-memory file contents to encode as
        ``file_data`` entries.
    """

    content: list[Dict[str, Any]] = []
    for text in _ensure_seq(texts):
        content.append(input_text(text))
    for url in _ensure_seq(file_urls):
        content.append(input_file_from_url(url))
    for file_id in _ensure_seq(file_ids):
        content.append(input_file_from_id(file_id))
    for filename, data in file_bytes or []:
        content.append(input_file_from_bytes(filename, data))

    payload: Dict[str, Any] = {
        "model": model,
        "input": [{"role": "user", "content": content}],
    }
    return client.responses.create(**payload)


def create_response_with_file_url(
    client: OpenAI,
    *,
    model: str,
    file_url: str,
    prompt: str,
) -> Any:
    """Backward compatible wrapper for a single URL and prompt."""

    return create_response(
        client,
        model=model,
        texts=[prompt],
        file_urls=[file_url],
    )
