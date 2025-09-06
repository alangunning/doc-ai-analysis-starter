from typer.testing import CliRunner

from doc_ai.cli import app


def test_pipeline_invalid_prompt(tmp_path):
    runner = CliRunner()
    missing = tmp_path / "missing.prompt.yaml"
    result = runner.invoke(app, ["pipeline", str(tmp_path), "--prompt", str(missing)])
    assert result.exit_code != 0
    assert "Prompt file not found" in result.output


def test_pipeline_invalid_model(tmp_path):
    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", str(tmp_path), "--model", "bogus-model"])
    assert result.exit_code != 0
    assert "Invalid value for '--model'" in result.output


def test_validate_invalid_prompt(tmp_path):
    runner = CliRunner()
    raw = tmp_path / "file.pdf"
    raw.write_text("raw")
    rendered = tmp_path / "file.pdf.converted.md"
    rendered.write_text("md")
    missing = tmp_path / "missing.prompt.yaml"
    result = runner.invoke(
        app,
        ["validate", str(raw), str(rendered), "--prompt", str(missing)],
    )
    assert result.exit_code != 0
    assert "Prompt file not found" in result.output


def test_validate_invalid_model(tmp_path):
    runner = CliRunner()
    raw = tmp_path / "file.pdf"
    raw.write_text("raw")
    rendered = tmp_path / "file.pdf.converted.md"
    rendered.write_text("md")
    result = runner.invoke(
        app,
        ["validate", str(raw), str(rendered), "--model", "bogus-model"],
    )
    assert result.exit_code != 0
    assert "Invalid value for '--model'" in result.output


def test_invalid_log_level():
    runner = CliRunner()
    result = runner.invoke(app, ["--log-level", "bogus", "config", "show"])
    assert result.exit_code != 0
    assert "Invalid log level" in result.stderr or "Invalid log level" in result.stdout
    assert "CRITICAL" in result.stderr or "CRITICAL" in result.stdout
