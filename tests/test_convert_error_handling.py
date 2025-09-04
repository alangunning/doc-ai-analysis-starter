import logging

from typer.testing import CliRunner

from doc_ai.cli import app
from doc_ai.converter import OutputFormat
from doc_ai.converter.path import convert_path, ConversionError



def test_convert_cli_handles_missing_path(tmp_path, monkeypatch):
    runner = CliRunner()
    missing = tmp_path / "missing.pdf"
    messages: list[str] = []

    def fake_error(msg, *args, **kwargs):
        messages.append(msg % args)

    monkeypatch.setattr("doc_ai.cli.convert.logger.error", fake_error)
    result = runner.invoke(app, ["convert", str(missing)])
    assert result.exit_code != 0
    assert any("Path does not exist" in m for m in messages)



def test_convert_path_warns_and_continues(tmp_path, monkeypatch, caplog):
    bad = tmp_path / "bad.pdf"
    bad.write_text("bad")
    good = tmp_path / "good.pdf"
    good.write_text("good")

    def fake_convert_files(src, outputs, return_status=True):
        if src == bad:
            raise ConversionError("boom")
        for out in outputs.values():
            out.write_text("ok", encoding="utf-8")
        return outputs, "OK"

    monkeypatch.setattr("doc_ai.converter.path.convert_files", fake_convert_files)

    with caplog.at_level(logging.WARNING):
        results = convert_path(tmp_path, [OutputFormat.TEXT])
    assert good in results
    assert bad not in results
    assert "Failed to convert" in caplog.text
    assert str(bad) in caplog.text

