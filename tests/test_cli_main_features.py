import logging
import sys

import pytest
from typer.testing import CliRunner

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


def test_logging_configuration(monkeypatch):
    runner = CliRunner()
    recorded = {}

    def fake_basicConfig(level=None, **kwargs):
        recorded["level"] = level

    monkeypatch.setattr(logging, "basicConfig", fake_basicConfig)
    result = runner.invoke(app, ["--log-level", "DEBUG", "config", "show"])
    assert result.exit_code == 0
    assert recorded["level"] == logging.DEBUG
    recorded.clear()
    result = runner.invoke(app, ["--verbose", "config", "show"])
    assert recorded["level"] == logging.DEBUG
