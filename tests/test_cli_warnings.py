import logging

from typer.testing import CliRunner

from doc_ai.cli import app
import doc_ai.cli as cli_module


def _no_op_convert_path(*args, **kwargs):
    return ["out"]


def test_warnings_logger_debug(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(cli_module, "convert_path", _no_op_convert_path)
    runner.invoke(app, ["--log-level", "DEBUG", "convert", "input"])
    assert logging.getLogger("py.warnings").level == logging.WARNING


def test_warnings_logger_quiet(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(cli_module, "convert_path", _no_op_convert_path)
    runner.invoke(app, ["--log-level", "WARNING", "convert", "input"])
    assert logging.getLogger("py.warnings").level == logging.ERROR
