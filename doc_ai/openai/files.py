"""Utilities for working with OpenAI file inputs.

This module provides helper functions to upload files using the
`/v1/files` endpoint and to generate file input payloads for the
`responses` API.  It supports file uploads from disk, file URLs and
in-memory bytes.
"""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import BinaryIO, Dict, Union

from openai import OpenAI


def _open_file(file: Union[str, Path, BinaryIO]):
    """Return a binary file handle for ``file``.

    ``file`` may be a path or an existing binary file object.
    """
    if hasattr(file, "read"):
        return file  # already a file-like object
    return open(Path(file), "rb")


def upload_file(client: OpenAI, file: Union[str, Path, BinaryIO], purpose: str = "user_data") -> str:
    """Upload a file to OpenAI and return its file id."""
    with _open_file(file) as fh:  # type: ignore[arg-type]
        response = client.files.create(file=fh, purpose=purpose)
    return response.id


def input_file_from_id(file_id: str) -> Dict[str, str]:
    """Create a file input payload referencing an uploaded file."""
    return {"type": "input_file", "file_id": file_id}


def input_file_from_url(file_url: str) -> Dict[str, str]:
    """Create a file input payload referencing an external file URL."""
    return {"type": "input_file", "file_url": file_url}


def input_file_from_path(client: OpenAI, path: Union[str, Path], purpose: str = "user_data") -> Dict[str, str]:
    """Upload ``path`` and return a file input payload referencing it."""
    file_id = upload_file(client, path, purpose)
    return input_file_from_id(file_id)


def input_file_from_bytes(filename: str, data: bytes) -> Dict[str, str]:
    """Create a base64 encoded file input payload.

    The correct mimetype is inferred from ``filename``.
    """
    mime, _ = mimetypes.guess_type(filename)
    mime = mime or "application/octet-stream"
    encoded = base64.b64encode(data).decode("utf-8")
    return {
        "type": "input_file",
        "filename": filename,
        "file_data": f"data:{mime};base64,{encoded}",
    }
