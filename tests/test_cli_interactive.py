from pathlib import Path
from unittest.mock import MagicMock
import os

from doc_ai import cli


def test_interactive_shell_cd(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "_print_banner", lambda: None)

    def fake_app(*, prog_name, args):
        raise SystemExit()

    monkeypatch.setattr(cli, "app", MagicMock(side_effect=fake_app))
    inputs = iter([f"cd {tmp_path}\n", "exit\n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    cwd = Path.cwd()
    try:
        cli._interactive_shell()
        assert Path.cwd() == tmp_path
    finally:
        os.chdir(cwd)
