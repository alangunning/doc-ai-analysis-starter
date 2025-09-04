from typer.testing import CliRunner

from doc_ai.cli import app


def test_show_completion():
    runner = CliRunner()
    result = runner.invoke(
        app, ["--show-completion"], env={"SHELL": "/bin/bash"}, prog_name="doc-ai"
    )
    assert result.exit_code == 0
    assert "_DOC_AI_COMPLETE=complete_bash" in result.stdout
