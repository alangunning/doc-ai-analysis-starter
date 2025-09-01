"""Embedding helpers for Markdown files."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
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
    client = OpenAI(api_key=token, base_url=base_url)

    for md_file in src_dir.rglob("*.md"):
        meta = load_metadata(md_file)
        file_hash = compute_hash(md_file)
        if meta.blake2b == file_hash and is_step_done(meta, "vector"):
            continue
        if meta.blake2b != file_hash:
            meta.blake2b = file_hash
            meta.extra = {}
        text = md_file.read_text(encoding="utf-8")
        kwargs: dict[str, object] = {
            "model": EMBED_MODEL,
            "input": text,
            "encoding_format": "float",
        }
        if EMBED_DIMENSIONS:
            kwargs["dimensions"] = int(EMBED_DIMENSIONS)

        success = False
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                resp = client.embeddings.create(**kwargs)
                success = True
                break
            except Exception as exc:  # pragma: no cover - network error
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

        embedding = resp.data[0].embedding
        out_file = md_file.with_suffix(".embedding.json")
        out_file.write_text(
            json.dumps({"file": str(md_file), "embedding": embedding}) + "\n",
            encoding="utf-8",
        )
        mark_step(meta, "vector", outputs=[out_file.name])
        save_metadata(md_file, meta)


__all__ = ["build_vector_store"]
