"""Embedding helpers for Markdown files."""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from ..metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "openai/text-embedding-3-small")
EMBED_DIMENSIONS = os.getenv("EMBED_DIMENSIONS")


def build_vector_store(src_dir: Path) -> None:
    """Generate embeddings for Markdown files in ``src_dir``."""

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")

    api_url = "https://models.github.ai/inference/embeddings"
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
        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        embedding = resp.json()["data"][0]["embedding"]
        out_file = md_file.with_suffix(".embedding.json")
        out_file.write_text(
            json.dumps({"file": str(md_file), "embedding": embedding}) + "\n",
            encoding="utf-8",
        )
        mark_step(meta, "vector")
        save_metadata(md_file, meta)


__all__ = ["build_vector_store"]
