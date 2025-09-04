import json
from unittest.mock import patch
import yaml
import logging
import pytest
from typer.testing import CliRunner

from doc_ai.cli import analyze_doc
from doc_ai.cli.analyze import app as analyze_app
from doc_ai.metadata import load_metadata, metadata_path


def test_analyze_doc_strips_fences_and_updates_metadata(tmp_path):
    doc_dir = tmp_path / "sec-form-4"
    doc_dir.mkdir()
    prompt = doc_dir / "sec-form-4.analysis.prompt.yaml"
    prompt.write_text(yaml.dump({"model": "test", "messages": []}))
    raw = doc_dir / "apple-sec-form-4.pdf"
    raw.write_text("raw")
    md = doc_dir / "apple-sec-form-4.pdf.converted.md"
    md.write_text("sample")
    with patch(
        "doc_ai.cli.run_prompt",
        return_value=("```json\n{\"foo\": 1}\n```", 0.0),
    ):
        analyze_doc(md)
    out_file = doc_dir / "apple-sec-form-4.pdf.analysis.json"
    assert out_file.exists()
    assert json.loads(out_file.read_text()) == {"foo": 1}
    assert not metadata_path(md).exists()
    meta = load_metadata(raw)
    assert meta.extra["outputs"]["analysis"] == [out_file.name]
    assert meta.extra["steps"]["analysis"] is True


def test_analyze_doc_reports_success(tmp_path, caplog):
    doc_dir = tmp_path / "sec-form-4"
    doc_dir.mkdir()
    prompt = doc_dir / "sec-form-4.analysis.prompt.yaml"
    prompt.write_text(yaml.dump({"model": "test", "messages": []}))
    raw = doc_dir / "apple-sec-form-4.pdf"
    raw.write_text("raw")
    md = doc_dir / "apple-sec-form-4.pdf.converted.md"
    md.write_text("sample")
    with patch("doc_ai.cli.run_prompt", return_value=("{}", 0.0)):
        with caplog.at_level(logging.INFO):
            analyze_doc(md)
    output = caplog.text
    assert "Analyzed" in output
    assert "apple-sec-form-4.pdf.analysis.json" in output
    assert "(SUCCESS)" in output


def test_analyze_doc_saves_text_when_json_invalid(tmp_path):
    doc_dir = tmp_path / "sec-form-4"
    doc_dir.mkdir()
    prompt = doc_dir / "sec-form-4.analysis.prompt.yaml"
    prompt.write_text(yaml.dump({"model": "test", "messages": []}))
    raw = doc_dir / "apple-sec-form-4.pdf"
    raw.write_text("raw")
    md = doc_dir / "apple-sec-form-4.pdf.converted.md"
    md.write_text("sample")
    with patch("doc_ai.cli.run_prompt", return_value=("not json", 0.0)):
        analyze_doc(md)
    out_file = doc_dir / "apple-sec-form-4.pdf.analysis.txt"
    assert out_file.exists()
    assert out_file.read_text() == "not json\n"
    meta = load_metadata(raw)
    assert meta.extra["outputs"]["analysis"] == [out_file.name]
    assert meta.extra["steps"]["analysis"] is True


def test_analyze_doc_requires_json(tmp_path):
    doc_dir = tmp_path / "sec-form-4"
    doc_dir.mkdir()
    prompt = doc_dir / "sec-form-4.analysis.prompt.yaml"
    prompt.write_text(yaml.dump({"model": "test", "messages": []}))
    raw = doc_dir / "apple-sec-form-4.pdf"
    raw.write_text("raw")
    md = doc_dir / "apple-sec-form-4.pdf.converted.md"
    md.write_text("sample")
    with patch("doc_ai.cli.run_prompt", return_value=("oops", 0.0)):
        with pytest.raises(ValueError):
            analyze_doc(md, require_json=True)
    assert not (doc_dir / "apple-sec-form-4.pdf.analysis.txt").exists()
    assert not metadata_path(md).exists()


def test_analyze_force_bypasses_metadata(tmp_path):
    doc_dir = tmp_path / "sec-form-4"
    doc_dir.mkdir()
    prompt = doc_dir / "sec-form-4.analysis.prompt.yaml"
    prompt.write_text(yaml.dump({"model": "test", "messages": []}))
    raw = doc_dir / "apple-sec-form-4.pdf"
    raw.write_text("raw")
    md = doc_dir / "apple-sec-form-4.pdf.converted.md"
    md.write_text("sample")
    with patch("doc_ai.cli.run_prompt", return_value=("{}", 0.0)):
        analyze_doc(md)

    calls: list[bool] = []

    def tracker(*args, **kwargs):
        calls.append(True)
        return "{}", 0.0

    with patch("doc_ai.cli.run_prompt", side_effect=tracker):
        analyze_doc(md)
    assert calls == []

    with patch("doc_ai.cli.run_prompt", side_effect=tracker):
        analyze_doc(md, force=True)
    assert calls == [True]


def test_analyze_doc_multiple_topics_and_skip(tmp_path):
    doc_dir = tmp_path / "sample"
    doc_dir.mkdir()
    prompt_a = doc_dir / "analysis_alpha.prompt.yaml"
    prompt_b = doc_dir / "analysis_beta.prompt.yaml"
    content = yaml.dump({"model": "test", "messages": []})
    prompt_a.write_text(content)
    prompt_b.write_text(content)
    raw = doc_dir / "doc.pdf"
    raw.write_text("raw")
    md = doc_dir / "doc.pdf.converted.md"
    md.write_text("sample")
    with patch("doc_ai.cli.run_prompt", return_value=("{}", 0.0)):
        analyze_doc(md, topic="alpha")
        analyze_doc(md, topic="beta")
    out_a = doc_dir / "doc.pdf.analysis.alpha.json"
    out_b = doc_dir / "doc.pdf.analysis.beta.json"
    assert out_a.exists() and out_b.exists()
    meta = load_metadata(raw)
    assert meta.extra["outputs"]["analysis:alpha"] == [out_a.name]
    assert meta.extra["outputs"]["analysis:beta"] == [out_b.name]
    calls: list[bool] = []

    def tracker(*args, **kwargs):
        calls.append(True)
        return "{}", 0.0

    with patch("doc_ai.cli.run_prompt", side_effect=tracker):
        analyze_doc(md, topic="alpha")
    assert calls == []


def test_analyze_cli_handles_generic_error(monkeypatch):
    runner = CliRunner()

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    messages: list[str] = []

    def fake_error(msg, *args, **kwargs):
        messages.append(msg % args)

    monkeypatch.setattr("doc_ai.cli.analyze.analyze_doc", boom)
    monkeypatch.setattr("doc_ai.cli.analyze.logger.error", fake_error)

    result = runner.invoke(analyze_app, ["sample.pdf"])
    assert result.exit_code == 1
    assert any("boom" in m for m in messages)


def test_analyze_cli_runs_topics(monkeypatch, tmp_path):
    src = tmp_path / "doc.pdf"
    src.write_text("raw")
    md = tmp_path / "doc.pdf.converted.md"
    md.write_text("sample")
    calls: list[str | None] = []

    def fake_analyze_doc(path, *args, topic=None, **kwargs):
        calls.append(topic)

    monkeypatch.setattr("doc_ai.cli.analyze.analyze_doc", fake_analyze_doc)
    runner = CliRunner()
    result = runner.invoke(
        analyze_app,
        ["--topic", "alpha", "--topic", "beta", str(src)],
    )
    assert result.exit_code == 0
    assert calls == ["alpha", "beta"]
