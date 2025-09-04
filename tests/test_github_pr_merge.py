import subprocess

import pytest

from doc_ai.github.pr import merge_pr


def test_merge_pr_missing_cli(monkeypatch):
    def mock_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr("doc_ai.github.pr.subprocess.run", mock_run)
    with pytest.raises(RuntimeError, match="GitHub CLI 'gh' not found"):
        merge_pr(1)


def test_merge_pr_failed(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["gh", "pr", "merge"])

    monkeypatch.setattr("doc_ai.github.pr.subprocess.run", mock_run)
    with pytest.raises(RuntimeError, match="Failed to merge PR #1"):
        merge_pr(1)
