import os

from typer.testing import CliRunner

from doc_ai.cli import app


def test_global_help_lists_commands():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert "Usage:" in result.stdout
    assert "convert" in result.stdout
    assert "config" in result.stdout
    assert "--install-completion" not in result.stdout


def test_validate_help_flag_shows_options():
    runner = CliRunner()
    result = runner.invoke(app, ["validate", "--help"])
    assert "--log-file" in result.stdout
    assert "--verbose" in result.stdout
    assert result.exit_code == 0


def test_config_sets_env(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        monkeypatch.setattr("doc_ai.cli.find_dotenv", lambda *a, **k: ".env")
        result = runner.invoke(app, ["config", "set", "TEST_VAR=value"])
        assert result.exit_code == 0
        assert os.getenv("TEST_VAR") == "value"
