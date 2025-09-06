# mypy: ignore-errors
"""Embedding helpers for Markdown files."""

from __future__ import annotations

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI
from rich.console import Console
from rich.progress import Progress

from doc_ai.logging import RedactFilter

from ..metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)
from .prompts import DEFAULT_MODEL_BASE_URL

EMBED_MODEL = os.getenv("EMBED_MODEL", "openai/text-embedding-3-small")
EMBED_DIMENSIONS = os.getenv("EMBED_DIMENSIONS")

_log = logging.getLogger(__name__)
_log.addFilter(RedactFilter())


def build_vector_store(
    src_dir: Path,
    *,
    fail_fast: bool = False,
    workers: int = 1,
    console: Console | None = None,
) -> None:
    """Generate embeddings for Markdown files in ``src_dir``.

    Args:
        src_dir: Directory containing Markdown files to embed.
        fail_fast: If ``True``, raise an exception when an HTTP request
            repeatedly fails. Otherwise, log the error and continue with the
            next file.
        workers: Number of threads used for concurrent processing.
    """

    base_url = (
        os.getenv("VECTOR_BASE_MODEL_URL")
        or os.getenv("BASE_MODEL_URL")
        or DEFAULT_MODEL_BASE_URL
    )
    api_key_var = "OPENAI_API_KEY" if "api.openai.com" in base_url else "GITHUB_TOKEN"
    token = os.getenv(api_key_var)
    if not token:
        raise RuntimeError(f"Missing required environment variable: {api_key_var}")
    client = OpenAI(api_key=token, base_url=base_url)

    md_files = list(src_dir.rglob("*.md"))

    def process(md_file: Path) -> None:
        meta = load_metadata(md_file)
        file_hash = compute_hash(md_file)
        if meta.blake2b == file_hash and is_step_done(meta, "vector"):
            return
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
            try:
                dims = int(EMBED_DIMENSIONS)
                if dims > 0:
                    kwargs["dimensions"] = dims
                else:
                    _log.warning(
                        "EMBED_DIMENSIONS must be a positive integer; got %s",
                        EMBED_DIMENSIONS,
                    )
            except ValueError:
                _log.warning(
                    "EMBED_DIMENSIONS must be a positive integer; got %s",
                    EMBED_DIMENSIONS,
                )

        success = False
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                resp = client.embeddings.create(**kwargs)
                success = True
                break
            except Exception as exc:  # pragma: no cover - network error
                wait = 2**attempt
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
            return

        embedding = resp.data[0].embedding
        out_file = md_file.with_suffix(".embedding.json")
        out_file.write_text(
            json.dumps({"file": str(md_file), "embedding": embedding}) + "\n",
            encoding="utf-8",
        )
        os.chmod(out_file, 0o600)
        mark_step(meta, "vector", outputs=[out_file.name])
        save_metadata(md_file, meta)

    console = console or Console()
    with Progress(transient=True, console=console) as progress:
        task = progress.add_task("Embedding markdown files", total=len(md_files))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process, md): md for md in md_files}
            for fut in as_completed(futures):
                md_file = futures[fut]
                progress.update(task, description=f"Embedding {md_file}")
                try:
                    fut.result()
                    progress.console.print(f"Embedded {md_file}")
                except Exception as exc:  # pragma: no cover - unexpected failure
                    progress.console.print(f"Failed to embed {md_file}: {exc}")
                    raise
                finally:
                    progress.advance(task)


__all__ = ["build_vector_store"]
