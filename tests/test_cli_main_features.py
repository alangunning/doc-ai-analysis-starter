import sys
import importlib
from pathlib import Path

import pytest
from typer.testing import CliRunner

import doc_ai.cli as cli_module
from doc_ai.cli import app, main, ASCII_ART


def test_main_no_tty_shows_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["cli.py"])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    called = False

    def fake_shell(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("doc_ai.cli.interactive_shell", fake_shell)
    with pytest.raises(SystemExit):
        main()
    out = capsys.readouterr().out
    assert "Usage:" in out
    assert not called


def test_banner_flag_control():
    runner = CliRunner()
    banner_line = ASCII_ART.splitlines()[1]
    result = runner.invoke(app, ["config", "show"])
    assert banner_line not in result.stdout
    result = runner.invoke(app, ["--banner", "config", "show"])
    assert banner_line in result.stdout


def test_interactive_startup_without_banner(monkeypatch):
    monkeypatch.delenv("DOC_AI_BANNER", raising=False)
    importlib.reload(cli_module)
    monkeypatch.setattr(sys, "argv", ["cli.py"])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    recorded = {}

    def fake_shell(app):
        recorded["shell"] = True

    def fake_print_banner():
        recorded["banner"] = True

    monkeypatch.setattr(cli_module, "interactive_shell", fake_shell)
    monkeypatch.setattr(cli_module, "_print_banner", fake_print_banner)
    cli_module.main()
    assert recorded.get("banner") is None
    assert recorded.get("shell") is True


def test_interactive_startup_with_banner_env(monkeypatch):
    monkeypatch.setenv("DOC_AI_BANNER", "1")
    importlib.reload(cli_module)
    monkeypatch.setattr(sys, "argv", ["cli.py"])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    recorded = {}

    def fake_shell(app):
        recorded["shell"] = True

    def fake_print_banner():
        recorded["banner"] = True

    monkeypatch.setattr(cli_module, "interactive_shell", fake_shell)
    monkeypatch.setattr(cli_module, "_print_banner", fake_print_banner)
    cli_module.main()
    assert recorded.get("banner") is True
    assert recorded.get("shell") is True


def test_logging_configuration(monkeypatch):
    runner = CliRunner()
    recorded: dict[str, object] = {}

    def fake_configure(level, log_file=None):  # pragma: no cover - simple proxy
        recorded["level"] = level
        recorded["log_file"] = log_file

    monkeypatch.setattr(cli_module, "configure_logging", fake_configure)
    result = runner.invoke(app, ["--log-level", "DEBUG", "--log-file", "x.log", "config", "show"])
    assert result.exit_code == 0
    assert recorded["level"] == "DEBUG"
    assert recorded["log_file"] == Path("x.log")
    recorded.clear()
    result = runner.invoke(app, ["--verbose", "config", "show"])
    assert recorded["level"] == "DEBUG"
