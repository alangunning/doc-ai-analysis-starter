"""Rendering validation helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from ..converter import OutputFormat
from ..openai import create_response
from .prompts import DEFAULT_MODEL_BASE_URL

OPENAI_BASE_URL = "https://api.openai.com/v1"

load_dotenv()


def validate_file(
    raw_path: Path | str,
    rendered_path: Path | str,
    fmt: OutputFormat,
    prompt_path: Path,
    model: str | None = None,
    base_url: str | None = None,
) -> Dict:
    """Validate ``rendered_path`` against ``raw_path`` for ``fmt``.

    The raw and rendered files may be local paths or remote URLs. Local files are
    uploaded as needed using the most suitable OpenAI file API; remote URLs are
    passed directly to the Responses API. GitHub Models do not offer file
    uploads, so when the base URL points at the GitHub provider (or is
    unspecified) the call is automatically routed to ``https://api.openai.com/v1``
    using the ``OPENAI_API_KEY`` token. Returns the model's JSON verdict as a
    dictionary.
    """

    base = (
        base_url
        or os.getenv("VALIDATE_BASE_MODEL_URL")
        or os.getenv("BASE_MODEL_URL")
        or DEFAULT_MODEL_BASE_URL
    )
    if not base or "models.github.ai" in base:
        base = OPENAI_BASE_URL
    api_key_var = "OPENAI_API_KEY" if "api.openai.com" in base else "GITHUB_TOKEN"
    client = OpenAI(api_key=os.getenv(api_key_var), base_url=base)

    spec = yaml.safe_load(prompt_path.read_text())
    system_msgs = [m["content"] for m in spec["messages"] if m.get("role") == "system"]
    user_msgs: List[str] = [m["content"] for m in spec["messages"] if m.get("role") == "user"]
    user_text = user_msgs[0].replace("{format}", fmt.value) if user_msgs else ""

    def _is_url(value: Path | str) -> bool:
        s = str(value)
        return s.startswith("http://") or s.startswith("https://")

    file_urls: List[str] = []
    file_paths: List[Path] = []
    for p in (raw_path, rendered_path):
        if _is_url(p):
            file_urls.append(str(p))
        else:
            file_paths.append(Path(p))

    result = create_response(
        client,
        model=model or spec["model"],
        system=system_msgs,
        texts=[user_text],
        file_urls=file_urls or None,
        file_paths=file_paths or None,
        file_purpose="assistants",
        **spec.get("modelParameters", {}),
    )

    text = result.output_text or "{}"
    return json.loads(text)


__all__ = ["validate_file"]
