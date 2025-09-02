"""Convenience helpers for creating Responses API requests."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Tuple, Union
from pathlib import Path
import json
import logging
import os

from openai import OpenAI

from .files import (
    input_file_from_bytes,
    input_file_from_id,
    input_file_from_url,
    upload_file,
)


def input_text(text: str, fmt: str = "text") -> Dict[str, Any]:
    """Create an ``input_text`` payload with an explicit format."""

    return {
        "type": "input_text",
        "text": {"value": text, "format": {"name": fmt}},
    }


def _ensure_seq(value: Union[Any, Sequence[Any], None]) -> Sequence[Any]:
    """Return ``value`` as a sequence."""

    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value]
    return value


def create_response(
    client: OpenAI,
    *,
    model: str,
    texts: Union[
        str,
        Tuple[str, str],
        Sequence[Union[str, Tuple[str, str]]],
        None,
    ] = None,
    file_urls: Union[str, Sequence[str], None] = None,
    file_ids: Union[str, Sequence[str], None] = None,
    file_bytes: Sequence[Tuple[str, bytes]] | None = None,
    file_paths: Union[str, Path, Sequence[Union[str, Path]], None] = None,
    system: Union[str, Sequence[str], None] = None,
    file_purpose: str | None = None,
    progress: Optional[Callable[[int], None]] = None,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any,
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
    file_paths:
        One or more local filesystem paths to upload before the request. Large
        files automatically switch to the resumable ``/v1/uploads`` API.
    system:
        Optional system message(s) to prepend to the request.
    file_purpose:
        Purpose used when uploading files. Defaults to ``"user_data"`` and may be
        overridden via the ``OPENAI_FILE_PURPOSE`` environment variable.
    progress:
        Optional callback invoked with the number of bytes uploaded. Useful for
        displaying progress bars.
    logger:
        Optional logger for emitting request and response payloads.
    """

    file_purpose = file_purpose or os.getenv("OPENAI_FILE_PURPOSE", "user_data")

    content: list[Dict[str, Any]] = []
    for text in _ensure_seq(texts):
        if isinstance(text, tuple):
            txt, fmt = text
            content.append(input_text(txt, fmt))
        else:
            content.append(input_text(text))
    for url in _ensure_seq(file_urls):
        content.append(input_file_from_url(url))
    for file_id in _ensure_seq(file_ids):
        content.append(input_file_from_id(file_id))
    for filename, data in file_bytes or []:
        content.append(input_file_from_bytes(filename, data))
    for path in _ensure_seq(file_paths):
        p = Path(path)
        file_id = upload_file(
            client,
            p,
            purpose=file_purpose,
            progress=progress,
            logger=logger,
        )
        content.append(input_file_from_id(file_id))

    messages: list[Dict[str, Any]] = []
    for sys in _ensure_seq(system):
        messages.append({"role": "system", "content": sys})
    messages.append({"role": "user", "content": content})

    payload: Dict[str, Any] = {"model": model, "input": messages}
    payload.update(kwargs)
    if logger:
        logger.debug(
            "Responses API request: %s",
            json.dumps(payload, indent=2),
        )
    result = client.responses.create(**payload)
    if logger:
        try:
            body = json.dumps(result.model_dump(), indent=2)
        except Exception:  # pragma: no cover - best effort
            body = str(result)
        logger.debug("Responses API response: %s", body)
    return result


def create_response_with_file_url(
    client: OpenAI,
    *,
    model: str,
    file_url: str,
    prompt: str,
    logger: Optional[logging.Logger] = None,
) -> Any:
    """Backward compatible wrapper for a single URL and prompt."""

    return create_response(
        client,
        model=model,
        texts=[prompt],
        file_urls=[file_url],
        logger=logger,
    )
