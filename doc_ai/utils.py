from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3


def http_get(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_RETRIES,
    **kwargs: Any,
) -> requests.Response:
    """Perform an HTTP GET with retry and timeout defaults."""

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
    return response


def sanitize_path(path: Path | str) -> Path:
    """Return a resolved ``Path`` ensuring the location exists."""

    try:
        return Path(path).expanduser().resolve(strict=True)
    except FileNotFoundError as exc:  # pragma: no cover - error handling
        raise ValueError(f"Path does not exist: {path}") from exc

