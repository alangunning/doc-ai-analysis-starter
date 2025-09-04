from typer.testing import CliRunner

from doc_ai.cli import app


def test_completion_scripts():
    runner = CliRunner()
    for shell in ("bash", "zsh", "fish"):
        result = runner.invoke(app, ["completion", shell])
        assert result.exit_code == 0
        assert f"_DOC_AI_COMPLETE=complete_{shell}" in result.stdout
