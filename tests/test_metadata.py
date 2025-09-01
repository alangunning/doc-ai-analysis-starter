from doc_ai.metadata import load_metadata, save_metadata, mark_step


def test_save_metadata_records_size_and_filename(tmp_path):
    doc = tmp_path / "file.txt"
    doc.write_text("hello world", encoding="utf-8")
    meta = load_metadata(doc)
    save_metadata(doc, meta)
    loaded = load_metadata(doc)
    assert loaded.size == doc.stat().st_size
    assert loaded.extra["filename"] == doc.name


def test_mark_step_records_outputs(tmp_path):
    doc = tmp_path / "data.txt"
    doc.write_text("content", encoding="utf-8")
    meta = load_metadata(doc)
    mark_step(meta, "conversion", outputs=["data.txt.converted.md"])
    save_metadata(doc, meta)
    loaded = load_metadata(doc)
    assert loaded.extra["outputs"]["conversion"] == ["data.txt.converted.md"]
