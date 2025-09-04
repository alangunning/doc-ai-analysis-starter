"""Utilities for working with OpenAI file inputs.

This module provides helper functions to upload files using the
`/v1/files` endpoint and to generate file input payloads for the
`responses` API.  It supports file uploads from disk, file URLs and
in-memory bytes.
"""
from __future__ import annotations

import base64
import json
import logging
import mimetypes
from pathlib import Path
import os
from typing import BinaryIO, Callable, Dict, List, Optional, Union

from openai import OpenAI

DEFAULT_CHUNK_SIZE = 64 * 1024 * 1024  # 64 MB per upload part


def _open_file(file: Union[str, Path, BinaryIO]) -> tuple[BinaryIO, bool]:
    """Return ``(fh, should_close)`` for ``file``.

    ``file`` may be a path or an existing binary file object. When the caller
    provides a file-like object we leave closing to the caller by returning
    ``should_close=False``.  When a path is supplied we open the file and
    indicate it should be closed after use.
    """
    if hasattr(file, "read"):
        return file, False  # already a file-like object
    try:
        return open(Path(file), "rb"), True
    except FileNotFoundError as exc:  # pragma: no cover - trivial
        raise ValueError(f"File not found: {file}") from exc


def upload_file(
    client: OpenAI,
    file: Union[str, Path, BinaryIO],
    purpose: str | None = None,
    *,
    use_upload: bool | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    mime_type: str | None = None,
    progress: Optional[Callable[[int], None]] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Upload ``file`` to OpenAI and return its ``file_id``.

    By default this uses the ``/v1/files`` endpoint.  For large files, set
    ``use_upload=True`` to leverage the resumable ``/v1/uploads`` API which
    splits the file into parts of ``chunk_size`` bytes. When ``progress`` is
    provided it is called with the number of bytes uploaded. When ``logger`` is
    supplied the request and response payloads are logged for debugging.
    """
    size = None
    if isinstance(file, (str, Path)):
        size = Path(file).stat().st_size
    elif hasattr(file, "seek"):
        pos = file.tell()
        file.seek(0, 2)
        size = file.tell()
        file.seek(pos)

    if purpose is None:
        purpose = os.getenv("OPENAI_FILE_PURPOSE", "user_data")

    if use_upload is None:
        env_flag = os.getenv("OPENAI_USE_UPLOAD")
        if env_flag is not None:
            use_upload = env_flag.lower() in {"1", "true", "yes", "on"}
        else:
            use_upload = size is not None and size > chunk_size

    if logger:
        name = (
            Path(file).name
            if isinstance(file, (str, Path))
            else Path(getattr(file, "name", "upload.bin")).name
        )
        logger.debug(
            "File upload request: %s",
            json.dumps(
                {
                    "filename": name,
                    "purpose": purpose,
                    "size": size,
                    "use_upload": use_upload,
                }
            ),
        )

    if use_upload:
        return upload_large_file(
            client,
            file,
            purpose=purpose,
            chunk_size=chunk_size,
            mime_type=mime_type,
            progress=progress,
            logger=logger,
        )

    fh, should_close = _open_file(file)
    try:
        response = client.files.create(file=fh, purpose=purpose)
        if logger:
            try:
                body = json.dumps(response.model_dump(), indent=2)
            except Exception:  # pragma: no cover - best effort
                body = str(response)
            logger.debug("File upload response: %s", body)
    finally:
        if should_close:
            fh.close()
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
    purpose: str | None = None,
    *,
    use_upload: bool | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    mime_type: str | None = None,
    progress: Optional[Callable[[int], None]] = None,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, str]:
    """Upload ``path`` and return a file input payload referencing it.

    ``progress`` and ``logger`` are forwarded to :func:`upload_file`.
    """
    file_id = upload_file(
        client,
        path,
        purpose=purpose,
        use_upload=use_upload,
        chunk_size=chunk_size,
        mime_type=mime_type,
        progress=progress,
        logger=logger,
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
    purpose: str | None = None,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    mime_type: str | None = None,
    progress: Optional[Callable[[int], None]] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Upload a file using the resumable ``/v1/uploads`` API.

    The file is split into chunks of ``chunk_size`` bytes which are uploaded
    sequentially as Parts before completing the Upload.  Returns the resulting
    ``file_id`` that can be used with other OpenAI APIs. If ``progress`` is
    provided it is invoked with the size of each chunk as it uploads. When
    ``logger`` is provided request and response payloads are recorded for
    debugging.
    """
    if purpose is None:
        purpose = os.getenv("OPENAI_FILE_PURPOSE", "user_data")

    # Determine filename and file size
    if isinstance(file, (str, Path)):
        path = Path(file)
        filename = path.name
        try:
            fh = open(path, "rb")
            size = path.stat().st_size
        except FileNotFoundError as exc:
            raise ValueError(f"File not found: {path}") from exc
        should_close = True
    else:
        fh = file  # type: ignore[assignment]
        filename = Path(getattr(file, "name", "upload.bin")).name
        fh.seek(0, 2)
        size = fh.tell()
        fh.seek(0)
        should_close = False

    mime = mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    if logger:
        logger.debug(
            "Upload create request: %s",
            json.dumps(
                {
                    "filename": filename,
                    "purpose": purpose,
                    "bytes": size,
                    "mime_type": mime,
                }
            ),
        )

    upload = client.uploads.create(
        purpose=purpose,
        filename=filename,
        bytes=size,
        mime_type=mime,
    )
    if logger:
        try:
            body = json.dumps(upload.model_dump(), indent=2)
        except Exception:  # pragma: no cover - best effort
            body = str(upload)
        logger.debug("Upload create response: %s", body)

    part_ids: List[str] = []
    try:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            part = client.uploads.parts.create(upload.id, data=chunk)
            part_ids.append(part.id)
            if logger:
                try:
                    part_body = json.dumps(part.model_dump(), indent=2)
                except Exception:  # pragma: no cover - best effort
                    part_body = str(part)
                logger.debug("Upload part response: %s", part_body)
            if progress:
                progress(len(chunk))
    finally:
        if should_close:
            fh.close()

    completed = client.uploads.complete(upload.id, part_ids=part_ids)
    if logger:
        try:
            comp_body = json.dumps(completed.model_dump(), indent=2)
        except Exception:  # pragma: no cover - best effort
            comp_body = str(completed)
        logger.debug("Upload complete response: %s", comp_body)
    return completed.file.id
