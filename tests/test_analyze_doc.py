import json
from io import StringIO
from unittest.mock import patch
import yaml
from rich.console import Console

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
    with patch("doc_ai.cli.run_prompt", return_value="```json\n{\"foo\": 1}\n```"):
        analyze_doc(md)
    out_file = doc_dir / "apple-sec-form-4.pdf.analysis.json"
    assert out_file.exists()
    assert json.loads(out_file.read_text()) == {"foo": 1}
    assert not metadata_path(md).exists()
    meta = load_metadata(raw)
    assert meta.extra["outputs"]["analysis"] == [out_file.name]
    assert meta.extra["steps"]["analysis"] is True


def test_analyze_doc_reports_success(tmp_path, monkeypatch):
    doc_dir = tmp_path / "sec-form-4"
    doc_dir.mkdir()
    prompt = doc_dir / "sec-form-4.analysis.prompt.yaml"
    prompt.write_text(yaml.dump({"model": "test", "messages": []}))
    raw = doc_dir / "apple-sec-form-4.pdf"
    raw.write_text("raw")
    md = doc_dir / "apple-sec-form-4.pdf.converted.md"
    md.write_text("sample")
    with patch("doc_ai.cli.run_prompt", return_value="{}"):
        buf = StringIO()
        monkeypatch.setattr(
            "doc_ai.cli.console", Console(file=buf, force_terminal=False, color_system=None)
        )
        analyze_doc(md)
        output = buf.getvalue()
    assert "Analyzed" in output
    assert "apple-sec-form-4.pdf.analysis.json" in output
    assert "(SUCCESS)" in output
