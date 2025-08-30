"""Pull request helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .prompts import run_prompt


def review_pr(pr_body: str, prompt_path: Path) -> str:
    """Run the PR review prompt against ``pr_body``."""

    return run_prompt(prompt_path, pr_body)


def merge_pr(pr_number: int) -> None:
    """Merge pull request ``pr_number`` using the GitHub CLI."""

    subprocess.run(["gh", "pr", "merge", str(pr_number), "--merge"], check=True)


__all__ = ["review_pr", "merge_pr"]
