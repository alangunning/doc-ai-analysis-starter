import subprocess

import pytest

pytest.importorskip("questionary")

from doc_ai.github.pr import merge_pr


def test_merge_pr_missing_cli(monkeypatch):
    def mock_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr("doc_ai.github.pr.subprocess.run", mock_run)
    with pytest.raises(RuntimeError, match="GitHub CLI 'gh' not found"):
        merge_pr(1, yes=True)


def test_merge_pr_failed(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["gh", "pr", "merge"])

    monkeypatch.setattr("doc_ai.github.pr.subprocess.run", mock_run)
    with pytest.raises(RuntimeError, match="Failed to merge PR #1"):
        merge_pr(1, yes=True)


def test_merge_pr_dry_run(monkeypatch):
    called = False

    def mock_run(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("doc_ai.github.pr.subprocess.run", mock_run)
    merge_pr(1, yes=True, dry_run=True)
    assert not called


def test_merge_pr_requires_confirmation(monkeypatch):
    class Dummy:
        def __init__(self, result):
            self._result = result

        def ask(self):
            return self._result

    monkeypatch.setattr(
        "doc_ai.github.pr.questionary.confirm",
        lambda *args, **kwargs: Dummy(False),
    )
    with pytest.raises(RuntimeError, match="Merge aborted"):
        merge_pr(1)
