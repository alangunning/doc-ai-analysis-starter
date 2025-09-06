import logging

from doc_ai.metadata import load_metadata, mark_step, save_metadata
from doc_ai.metadata.dublin_core import DublinCoreDocument


def test_save_metadata_records_size_and_filename(tmp_path):
    doc = tmp_path / "file.txt"
    doc.write_text("hello world", encoding="utf-8")
    meta = load_metadata(doc)
    save_metadata(doc, meta)
    loaded = load_metadata(doc)
    assert loaded.size == doc.stat().st_size
    assert loaded.extra["filename"] == doc.name


def test_mark_step_records_outputs_and_inputs(tmp_path):
    doc = tmp_path / "data.txt"
    doc.write_text("content", encoding="utf-8")
    meta = load_metadata(doc)
    mark_step(
        meta,
        "conversion",
        outputs=["data.txt.converted.md"],
        inputs={"source": str(doc), "formats": ["markdown"]},
    )
    save_metadata(doc, meta)
    loaded = load_metadata(doc)
    assert loaded.extra["outputs"]["conversion"] == ["data.txt.converted.md"]
    assert loaded.extra["inputs"]["conversion"]["formats"] == ["markdown"]
    assert loaded.extra["inputs"]["conversion"]["source"] == str(doc)


def test_decode_content_invalid_logs_warning(caplog):
    with caplog.at_level(logging.WARNING):
        assert DublinCoreDocument.decode_content("!!!") is None
    assert "Failed to decode content" in caplog.text
