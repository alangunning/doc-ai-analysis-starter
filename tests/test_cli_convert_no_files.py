from typer.testing import CliRunner
from doc_ai.cli import app


def test_convert_cli_reports_when_no_files(monkeypatch, tmp_path):
    def fake_convert_path(source, fmts):
        return {}
    monkeypatch.setattr("doc_ai.cli.convert_path", fake_convert_path)
    runner = CliRunner()
    result = runner.invoke(app, ["convert", "-f", "markdown", str(tmp_path)])
    assert "No new files to process." in result.stdout

