import json
from unittest.mock import patch
import yaml

from doc_ai.cli import analyze_doc
from doc_ai.metadata import load_metadata, metadata_path


def test_analyze_doc_strips_fences_and_updates_metadata(tmp_path):
    prompt = tmp_path / "sec-form-4.prompt.yaml"
    prompt.write_text(yaml.dump({"model": "test", "messages": []}))
    raw = tmp_path / "apple-sec-form-4.pdf"
    raw.write_text("raw")
    md = tmp_path / "apple-sec-form-4.pdf.converted.md"
    md.write_text("sample")
    with patch("doc_ai.cli.run_prompt", return_value="```json\n{\"foo\": 1}\n```"):
        analyze_doc(prompt, md)
    out_file = tmp_path / "apple-sec-form-4.sec-form-4.json"
    assert out_file.exists()
    assert json.loads(out_file.read_text()) == {"foo": 1}
    assert not metadata_path(md).exists()
    meta = load_metadata(raw)
    assert meta.extra["outputs"]["analysis"] == [out_file.name]
    assert meta.extra["steps"]["analysis"] is True
