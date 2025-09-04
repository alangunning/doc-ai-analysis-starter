import json
from unittest.mock import patch
import yaml
import logging
import pytest

from doc_ai.cli import analyze_doc
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
