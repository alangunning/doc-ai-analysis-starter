"""Embedding helpers for Markdown files."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests import RequestException
import logging

from ..metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)
from .prompts import DEFAULT_MODEL_BASE_URL

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "openai/text-embedding-3-small")
EMBED_DIMENSIONS = os.getenv("EMBED_DIMENSIONS")

_log = logging.getLogger(__name__)


def build_vector_store(src_dir: Path, *, fail_fast: bool = False) -> None:
    """Generate embeddings for Markdown files in ``src_dir``.

    Args:
        src_dir: Directory containing Markdown files to embed.
        fail_fast: If ``True``, raise an exception when an HTTP request
            repeatedly fails. Otherwise, log the error and continue with the
            next file.
    """

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")
    base_url = (
        os.getenv("VECTOR_BASE_MODEL_URL")
        or os.getenv("BASE_MODEL_URL")
        or DEFAULT_MODEL_BASE_URL
    )
    api_url = f"{base_url}/inference/embeddings"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    for md_file in src_dir.rglob("*.md"):
        meta = load_metadata(md_file)
        file_hash = compute_hash(md_file)
        if meta.blake2b == file_hash and is_step_done(meta, "vector"):
            continue
        if meta.blake2b != file_hash:
            meta.blake2b = file_hash
            meta.extra = {}
        text = md_file.read_text(encoding="utf-8")
        payload: dict[str, object] = {
            "model": EMBED_MODEL,
            "input": [text],
            "encoding_format": "float",
        }
        if EMBED_DIMENSIONS:
            payload["dimensions"] = int(EMBED_DIMENSIONS)

        success = False
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                resp = requests.post(
                    api_url, headers=headers, json=payload, timeout=60
                )
                resp.raise_for_status()
                success = True
                break
            except RequestException as exc:
                wait = 2 ** attempt
                _log.error(
                    "Embedding request failed for %s (attempt %s/%s): %s",
                    md_file,
                    attempt,
                    max_attempts,
                    exc,
                )
                if attempt == max_attempts:
                    if fail_fast:
                        raise
                    _log.error("Skipping %s after repeated failures", md_file)
                    break
                time.sleep(wait)

        if not success:
            continue

        embedding = resp.json()["data"][0]["embedding"]
        out_file = md_file.with_suffix(".embedding.json")
        out_file.write_text(
            json.dumps({"file": str(md_file), "embedding": embedding}) + "\n",
            encoding="utf-8",
        )
        mark_step(meta, "vector")
        save_metadata(md_file, meta)


__all__ = ["build_vector_store"]
