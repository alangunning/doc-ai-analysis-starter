from typer.testing import CliRunner

from doc_ai.cli import app


def test_validate_mismatch_exits_with_message(monkeypatch, tmp_path):
    runner = CliRunner()
    raw = tmp_path / "file.pdf"
    raw.write_text("raw")
    rendered = tmp_path / "file.pdf.converted.md"
    rendered.write_text("converted")

    def fake_validate_file(raw_p, rendered_p, fmt, prompt_p, **kwargs):
        return {"match": False}

    monkeypatch.setattr("doc_ai.cli.validate_file", fake_validate_file)

    result = runner.invoke(app, ["validate", str(raw), str(rendered)])

    assert result.exit_code == 1
    assert result.stdout == ""
    lines = result.stderr.strip().splitlines()
    message = lines[1].strip().strip("│").strip()
    assert message == "Mismatch detected: {'match': False}"
