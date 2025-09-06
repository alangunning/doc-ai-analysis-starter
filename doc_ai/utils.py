from __future__ import annotations

from pathlib import Path
from typing import Any, Set

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from slugify import slugify

DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3


def http_get(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_RETRIES,
    suppress_raise: bool = False,
    **kwargs: Any,
) -> requests.Response:
    """Perform an HTTP GET with retry and timeout defaults.

    ``requests`` does not raise for HTTP error responses by default. To avoid
    silently ignoring client or server errors, this helper now calls
    :meth:`requests.Response.raise_for_status` on the returned response unless
    ``suppress_raise`` is ``True``.
    """

    retry = Retry(
        total=max_retries,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    with requests.Session() as session:
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        response = session.get(url, timeout=timeout, **kwargs)
        if not suppress_raise:
            response.raise_for_status()
    return response


def sanitize_path(path: Path | str) -> Path:
    """Return a resolved ``Path`` ensuring the location exists."""

    try:
        return Path(path).expanduser().resolve(strict=True)
    except FileNotFoundError as exc:  # pragma: no cover - error handling
        raise ValueError(f"Path does not exist: {path}") from exc


def sanitize_filename(name: str, existing: Set[str] | None = None) -> str:
    """Return a slugified ``name`` ensuring uniqueness within ``existing``.

    Preserves the original file extension and appends a numeric suffix when
    necessary to avoid duplicates.
    """

    p = Path(name)
    stem = slugify(p.stem) or "file"
    suffix = p.suffix
    candidate = f"{stem}{suffix}"
    if existing is None:
        return candidate
    new_name = candidate
    counter = 1
    while new_name in existing:
        new_name = f"{stem}-{counter}{suffix}"
        counter += 1
    return new_name
