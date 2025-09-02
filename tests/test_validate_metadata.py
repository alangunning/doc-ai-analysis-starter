from pathlib import Path

import pytest

from doc_ai.cli.utils import validate_doc
from doc_ai.converter import OutputFormat
from doc_ai.metadata import load_metadata


def _create_files(tmp_path: Path):
    raw = tmp_path / "doc.pdf"
    raw.write_bytes(b"raw")
    rendered = tmp_path / "doc.pdf.converted.md"
    rendered.write_text("content", encoding="utf-8")
    prompt = tmp_path / "doc.validate.prompt.yaml"
    prompt.write_text("prompt", encoding="utf-8")
    return raw, rendered, prompt


def test_validate_doc_records_metadata(tmp_path):
    raw, rendered, prompt = _create_files(tmp_path)

    def good_validate_file(raw_p, rendered_p, fmt, prompt_p, **kwargs):
        return {"match": True}

    validate_doc(
        raw,
        rendered,
        fmt=OutputFormat.MARKDOWN,
        prompt=prompt,
        model="gpt-test",
        base_url="https://example.com",
        validate_file_func=good_validate_file,
    )

    meta = load_metadata(raw)
    inputs = meta.extra["inputs"]["validation"]
    assert meta.extra["steps"]["validation"] is True
    assert inputs["model"] == "gpt-test"
    assert inputs["document"] == str(raw)
    assert inputs["verdict"]["match"] is True
    assert "validated_at" in inputs


def test_validate_doc_records_invalid(tmp_path):
    raw, rendered, prompt = _create_files(tmp_path)

    def bad_validate_file(raw_p, rendered_p, fmt, prompt_p, **kwargs):
        return {"match": False, "issues": ["x"]}

    with pytest.raises(RuntimeError):
        validate_doc(
            raw,
            rendered,
            fmt=OutputFormat.MARKDOWN,
            prompt=prompt,
            model="gpt-test",
            base_url="https://example.com",
            validate_file_func=bad_validate_file,
        )

    meta = load_metadata(raw)
    inputs = meta.extra["inputs"]["validation"]
    assert meta.extra["steps"]["validation"] is False
    assert inputs["verdict"]["match"] is False
