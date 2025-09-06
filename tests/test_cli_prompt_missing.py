import sys
from pathlib import Path

from doc_ai.cli.utils import prompt_for_missing


class Dummy:
    def __init__(self, ans: str):
        self.ans = ans

    def ask(self) -> str:
        return self.ans


def test_prompt_for_missing_returns_answer(monkeypatch):
    monkeypatch.setattr("questionary.path", lambda message: Dummy("/tmp/file"))
    monkeypatch.setenv("INTERACTIVE", "true")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)

    result = prompt_for_missing(None, "File?", path=True)
    assert isinstance(result, Path)
    assert str(result) == "/tmp/file"


def test_prompt_for_missing_non_interactive(monkeypatch):
    monkeypatch.setenv("INTERACTIVE", "true")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    def boom(message):
        raise AssertionError("prompt should not run")

    monkeypatch.setattr("questionary.path", boom)
    assert prompt_for_missing(None, "File?", path=True) is None
