"""Metadata utilities for ai_doc_analysis_starter."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .dublin_core import DublinCoreDocument


_DEF_STEP_KEY = "steps"


def metadata_path(doc_path: Path) -> Path:
    """Return the companion Dublin Core metadata path for ``doc_path``."""
    return doc_path.with_suffix(doc_path.suffix + ".dc.json")


def load_metadata(doc_path: Path) -> DublinCoreDocument:
    """Load Dublin Core metadata for ``doc_path`` if present."""
    meta_file = metadata_path(doc_path)
    if meta_file.exists():
        return DublinCoreDocument.from_json(meta_file.read_text(encoding="utf-8"))
    return DublinCoreDocument()


def save_metadata(doc_path: Path, meta: DublinCoreDocument) -> None:
    """Persist ``meta`` alongside ``doc_path``."""
    meta_file = metadata_path(doc_path)
    meta_file.write_text(meta.to_json(), encoding="utf-8")


def compute_hash(doc_path: Path) -> str:
    """Return a blake2b checksum of the file at ``doc_path``."""
    return hashlib.blake2b(doc_path.read_bytes()).hexdigest()


def is_step_done(meta: DublinCoreDocument, step: str) -> bool:
    """Check whether ``step`` was recorded as completed in ``meta``."""
    if meta.extra is None:
        return False
    steps = meta.extra.get(_DEF_STEP_KEY, {})
    return bool(steps.get(step))


def mark_step(meta: DublinCoreDocument, step: str, done: bool = True) -> None:
    """Record completion state for ``step`` in ``meta``."""
    extra = meta.extra or {}
    steps = extra.get(_DEF_STEP_KEY, {})
    steps[step] = done
    extra[_DEF_STEP_KEY] = steps
    meta.extra = extra


__all__ = [
    "DublinCoreDocument",
    "metadata_path",
    "load_metadata",
    "save_metadata",
    "compute_hash",
    "is_step_done",
    "mark_step",
]
