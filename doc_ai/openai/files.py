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
from typing import BinaryIO, Callable, Dict, List, Optional, Union

from openai import OpenAI

DEFAULT_CHUNK_SIZE = 64 * 1024 * 1024  # 64 MB per upload part


def _open_file(file: Union[str, Path, BinaryIO]):
    """Return a binary file handle for ``file``.

    ``file`` may be a path or an existing binary file object.
    """
    if hasattr(file, "read"):
        return file  # already a file-like object
    return open(Path(file), "rb")


def upload_file(
    client: OpenAI,
    file: Union[str, Path, BinaryIO],
    purpose: str = "user_data",
    *,
    use_upload: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    mime_type: str | None = None,
    progress: Optional[Callable[[int], None]] = None,
) -> str:
    """Upload ``file`` to OpenAI and return its ``file_id``.

    By default this uses the ``/v1/files`` endpoint.  For large files, set
    ``use_upload=True`` to leverage the resumable ``/v1/uploads`` API which
    splits the file into parts of ``chunk_size`` bytes. When ``progress`` is
    provided it is called with the number of bytes uploaded.
    """
    if use_upload:
        return upload_large_file(
            client,
            file,
            purpose=purpose,
            chunk_size=chunk_size,
            mime_type=mime_type,
            progress=progress,
        )

    size = None
    if isinstance(file, (str, Path)):
        size = Path(file).stat().st_size
    elif hasattr(file, "seek"):
        pos = file.tell()
        file.seek(0, 2)
        size = file.tell()
        file.seek(pos)

    with _open_file(file) as fh:  # type: ignore[arg-type]
        response = client.files.create(file=fh, purpose=purpose)
    if progress and size is not None:
        progress(size)
    return response.id


def input_file_from_id(file_id: str) -> Dict[str, str]:
    """Create a file input payload referencing an uploaded file."""
    return {"type": "input_file", "file_id": file_id}


def input_file_from_url(file_url: str) -> Dict[str, str]:
    """Create a file input payload referencing an external file URL."""
    return {"type": "input_file", "file_url": file_url}


def input_file_from_path(
    client: OpenAI,
    path: Union[str, Path],
    purpose: str = "user_data",
    *,
    use_upload: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    mime_type: str | None = None,
    progress: Optional[Callable[[int], None]] = None,
) -> Dict[str, str]:
    """Upload ``path`` and return a file input payload referencing it.

    ``progress`` is forwarded to :func:`upload_file`.
    """
    file_id = upload_file(
        client,
        path,
        purpose=purpose,
        use_upload=use_upload,
        chunk_size=chunk_size,
        mime_type=mime_type,
        progress=progress,
    )
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


def upload_large_file(
    client: OpenAI,
    file: Union[str, Path, BinaryIO],
    purpose: str = "user_data",
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    mime_type: str | None = None,
    progress: Optional[Callable[[int], None]] = None,
) -> str:
    """Upload a file using the resumable ``/v1/uploads`` API.

    The file is split into chunks of ``chunk_size`` bytes which are uploaded
    sequentially as Parts before completing the Upload.  Returns the resulting
    ``file_id`` that can be used with other OpenAI APIs. If ``progress`` is
    provided it is invoked with the size of each chunk as it uploads.
    """
    # Determine filename and file size
    if isinstance(file, (str, Path)):
        path = Path(file)
        filename = path.name
        size = path.stat().st_size
        fh = open(path, "rb")
    else:
        fh = file  # type: ignore[assignment]
        filename = Path(getattr(file, "name", "upload.bin")).name
        fh.seek(0, 2)
        size = fh.tell()
        fh.seek(0)

    mime = mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    upload = client.uploads.create(
        purpose=purpose,
        filename=filename,
        bytes=size,
        mime_type=mime,
    )

    part_ids: List[str] = []
    try:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            part = client.uploads.parts.create(upload.id, data=chunk)
            part_ids.append(part.id)
            if progress:
                progress(len(chunk))
    finally:
        fh.close()

    completed = client.uploads.complete(upload.id, part_ids=part_ids)
    return completed.file.id
