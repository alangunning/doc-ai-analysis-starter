"""Ensure project root is on sys.path for tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _set_default_embed_dimensions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide a sane default for EMBED_DIMENSIONS in tests."""
    monkeypatch.setenv("EMBED_DIMENSIONS", "64")
