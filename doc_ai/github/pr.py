"""Pull request helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .prompts import run_prompt


def review_pr(
    pr_body: str,
    prompt_path: Path,
    *,
    model: str | None = None,
    base_url: str | None = None,
) -> str:
    """Run the PR review prompt against ``pr_body``."""
    output, _ = run_prompt(
        prompt_path, pr_body, model=model, base_url=base_url
    )
    return output


def merge_pr(pr_number: int) -> None:
    """Merge pull request ``pr_number`` using the GitHub CLI."""
    try:
        subprocess.run(["gh", "pr", "merge", str(pr_number), "--merge"], check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("GitHub CLI 'gh' not found; ensure it is installed and on PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Failed to merge PR #{pr_number}: {exc}") from exc


__all__ = ["review_pr", "merge_pr"]
