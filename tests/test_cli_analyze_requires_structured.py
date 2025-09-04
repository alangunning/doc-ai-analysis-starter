from typer.testing import CliRunner

from doc_ai.cli import app


def test_cli_analyze_requires_structured(monkeypatch, tmp_path):
    runner = CliRunner()

    # Prepare a converted document and its raw counterpart
    raw = tmp_path / "file.pdf"
    raw.write_text("raw")
    md = tmp_path / "file.pdf.converted.md"
    md.write_text("content")

    # Simulate model returning unstructured output
    def fake_run_prompt(*args, **kwargs):
        return "not json", 0.0

    monkeypatch.setattr("doc_ai.cli.run_prompt", fake_run_prompt)

    result = runner.invoke(app, ["analyze", "--require-structured", str(md)])

    assert result.exit_code == 1
    assert "Analysis result is not valid JSON" in result.output
