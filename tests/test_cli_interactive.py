from pathlib import Path
from unittest.mock import MagicMock
import os

from doc_ai import cli
from doc_ai.cli import interactive_shell, get_completions


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
