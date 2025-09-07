"""Convenience helpers for creating Responses API requests."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Sequence, Tuple, Union

from openai import OpenAIError

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from openai import OpenAI

from .files import (
    input_file_from_bytes,
    input_file_from_id,
    input_file_from_url,
    upload_file,
)

ALLOWED_PARAMS = {
    "temperature",
    "top_p",
    "tools",
    "tool_choice",
    "parallel_tool_calls",
    "metadata",
    "max_output_tokens",
    "text",
}


def input_text(text: str) -> Dict[str, Any]:
    """Create a basic ``input_text`` payload."""
    return {"type": "input_text", "text": text}


def _ensure_seq(value: Union[Any, Sequence[Any], None]) -> Sequence[Any]:
    """Return ``value`` as a sequence."""

    if value is None:
        return []
    if isinstance(value, (str, bytes, os.PathLike)):
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
    file_paths: Union[str, Path, Sequence[Union[str, Path]], None] = None,
    system: Union[str, Sequence[str], None] = None,
    file_purpose: str | None = None,
    progress: Optional[Callable[[int], None]] = None,
    logger: Optional[logging.Logger] = None,
    retries: int = 3,
    request_timeout: float | None = None,
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
    retries:
        Number of times to retry failed API calls. Defaults to ``3``.
    request_timeout:
        Timeout in seconds for the API request.
    """

    file_purpose = file_purpose or os.getenv("OPENAI_FILE_PURPOSE", "user_data")

    content: list[Dict[str, Any]] = []
    for text in _ensure_seq(texts):
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
        messages.append({"role": "system", "content": [input_text(sys)]})
    messages.append({"role": "user", "content": content})

    payload: Dict[str, Any] = {"model": model, "input": messages}
    for key, value in kwargs.items():
        if key in ALLOWED_PARAMS:
            payload[key] = value
    if logger:
        logger.debug(
            "Responses API request: %s",
            json.dumps(payload, indent=2),
        )

    result = None
    call_kwargs = dict(payload)
    if request_timeout is not None:
        call_kwargs["timeout"] = request_timeout

    for attempt in range(retries):
        try:
            result = client.responses.create(**call_kwargs)
            break
        except OpenAIError as exc:  # pragma: no cover - network failures
            if logger:
                logger.warning(
                    "Responses API request failed",
                    extra={"attempt": attempt + 1, "error": str(exc)},
                )
            if attempt == retries - 1:
                if logger:
                    logger.error(
                        "Responses API request failed after %s attempts",
                        retries,
                        extra={"error": str(exc)},
                    )
                raise RuntimeError(
                    f"Responses API request failed after {retries} attempts"
                ) from exc
            time.sleep(2**attempt)

    if logger and result is not None:
        try:
            body = json.dumps(result.model_dump(), indent=2)
        except (TypeError, ValueError):  # pragma: no cover - best effort
            logger.exception("Failed to serialize Responses API output")
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
