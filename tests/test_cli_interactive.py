from pathlib import Path
from unittest.mock import MagicMock
from typing import Callable
import os

from doc_ai import cli
from doc_ai.cli import interactive_shell, get_completions
import doc_ai.cli.interactive as interactive_mod
import sys


def test_interactive_shell_cd(monkeypatch, tmp_path):
    def fake_app(*, prog_name, args):
        raise SystemExit()

    app_mock = MagicMock(side_effect=fake_app)
    inputs = iter([f"cd {tmp_path}\n", "exit\n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    cwd = Path.cwd()
    try:
        interactive_shell(app_mock, print_banner=lambda: None, prog_name="test")
        assert Path.cwd() == tmp_path
    finally:
        os.chdir(cwd)


def test_completions_top_level():
    opts = get_completions(cli.app, "", "")
    assert "convert" in opts


def test_completions_options():
    opts = get_completions(cli.app, "convert --f", "--f")
    assert any(opt.startswith("--format") for opt in opts)


def test_cd_path_completion(tmp_path):
    sub = tmp_path / "subdir"
    sub.mkdir()
    cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        opts = get_completions(cli.app, "cd s", "s")
        assert "subdir/" in opts
    finally:
        os.chdir(cwd)


def test_argument_path_completion(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("x")
    cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        opts = get_completions(cli.app, "convert f", "f")
        assert "file.txt" in opts
    finally:
        os.chdir(cwd)


def test_cd_nested_completion(tmp_path):
    child = tmp_path / "parent" / "child"
    child.mkdir(parents=True)
    cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        opts = get_completions(cli.app, "cd parent/", "")
        assert "child/" in opts
        assert all(not opt.startswith("parent/") for opt in opts)
    finally:
        os.chdir(cwd)


def test_argument_nested_path_completion(tmp_path):
    parent = tmp_path / "parent"
    parent.mkdir()
    file = parent / "file.txt"
    file.write_text("x")
    cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        opts = get_completions(cli.app, "convert parent/", "")
        assert "file.txt" in opts
        assert all(not opt.startswith("parent/") for opt in opts)
    finally:
        os.chdir(cwd)


def test_tab_completion(monkeypatch, tmp_path):
    """Ensure the readline completer uses ``get_completions``."""

    class FakeReadline:
        def __init__(self) -> None:
            self.completer = None

        def read_history_file(self, path):
            pass

        def write_history_file(self, path):
            pass

        def set_completer(self, func):
            self.completer = func

        def parse_and_bind(self, string):
            pass

        def get_line_buffer(self):
            return "co"

    fake_readline = FakeReadline()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setitem(sys.modules, "readline", fake_readline)

    def fake_get_completions(app, buffer, text):
        return ["convert"]

    monkeypatch.setattr(interactive_mod, "get_completions", fake_get_completions)

    def fake_app(*, prog_name, args):
        raise SystemExit()

    app_mock = MagicMock(side_effect=fake_app)
    inputs = iter(["exit\n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    interactive_shell(app_mock, print_banner=lambda: None, prog_name="test")
    assert fake_readline.completer("", 0) == "convert"


def test_history_persistence(monkeypatch, tmp_path):
    """The shell should persist history to the user's home directory."""

    written: list[Path] = []

    class FakeReadline:
        def read_history_file(self, path):
            pass

        def write_history_file(self, path):
            written.append(Path(path))

        def set_completer(self, func):
            pass

        def parse_and_bind(self, string):
            pass

        def get_line_buffer(self):
            return ""

    fake_readline = FakeReadline()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setitem(sys.modules, "readline", fake_readline)

    registered: list[Callable[[], None]] = []
    monkeypatch.setattr(
        interactive_mod, "atexit", MagicMock(register=lambda f: registered.append(f))
    )

    def fake_app(*, prog_name, args):
        raise SystemExit()

    app_mock = MagicMock(side_effect=fake_app)
    inputs = iter(["exit\n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    interactive_shell(app_mock, print_banner=lambda: None, prog_name="test")
    assert registered, "history writer not registered"
    for func in registered:
        func()
    assert written and written[0] == tmp_path / ".doc_ai_history"
