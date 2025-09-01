"""Convenience helpers for creating Responses API requests."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Tuple, Union
from pathlib import Path

from openai import OpenAI

from .files import (
    DEFAULT_CHUNK_SIZE,
    input_file_from_bytes,
    input_file_from_id,
    input_file_from_url,
    upload_file,
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
    file_paths: Union[str, Path, Sequence[Union[str, Path]], None] = None,
    system: Union[str, Sequence[str], None] = None,
    file_purpose: str = "user_data",
    progress: Optional[Callable[[int], None]] = None,
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
        One or more local filesystem paths to upload before the request. Files
        larger than ``DEFAULT_CHUNK_SIZE`` will use the resumable ``/v1/uploads``
        API automatically.
    system:
        Optional system message(s) to prepend to the request.
    file_purpose:
        Purpose used when uploading files. Defaults to ``"user_data"``.
    progress:
        Optional callback invoked with the number of bytes uploaded. Useful for
        displaying progress bars.
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
    for path in _ensure_seq(file_paths):
        p = Path(path)
        use_upload = p.stat().st_size > DEFAULT_CHUNK_SIZE
        file_id = upload_file(
            client,
            p,
            purpose=file_purpose,
            use_upload=use_upload,
            progress=progress,
        )
        content.append(input_file_from_id(file_id))

    messages: list[Dict[str, Any]] = []
    for sys in _ensure_seq(system):
        messages.append({"role": "system", "content": sys})
    messages.append({"role": "user", "content": content})

    payload: Dict[str, Any] = {"model": model, "input": messages}
    payload.update(kwargs)
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
