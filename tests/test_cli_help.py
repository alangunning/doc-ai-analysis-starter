from typer.testing import CliRunner
from doc_ai.cli import app


def test_help_command_lists_commands():
    runner = CliRunner()
    result = runner.invoke(app, ["help"])
    assert "Usage:" in result.stdout
    assert "convert" in result.stdout


def test_help_validate_shows_options():
    runner = CliRunner()
    result = runner.invoke(app, ["help", "validate"])
    assert "--log-file" in result.stdout
    assert "--verbose" in result.stdout


def test_validate_help_alias():
    runner = CliRunner()
    result = runner.invoke(app, ["validate", "help"])
    assert "--log-file" in result.stdout
    assert result.exit_code == 0
