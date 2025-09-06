#!/usr/bin/env python3
"""Entry point wrapper for doc_ai CLI."""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path[0] = str(Path(__file__).resolve().parent.parent)

from doc_ai.cli import main

if __name__ == "__main__":
    main()
