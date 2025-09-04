from pathlib import Path
from unittest.mock import patch

from doc_ai.cli import pipeline


def test_pipeline_skips_converted(tmp_path):
    src = tmp_path / "docs"
    src.mkdir()
    raw = src / "sample.pdf"
    raw.write_text("raw")
    md = src / "sample.pdf.converted.md"
    md.write_text("converted")
    # A file inside a path with '.converted' should be ignored
    nested_dir = src / "nested.converted"
    nested_dir.mkdir()
    ignored = nested_dir / "ignored.pdf"
    ignored.write_text("raw")

    calls = []

    def fake_validate(raw_file, rendered, *args, **kwargs):
        calls.append(("validate", raw_file, rendered))

    def fake_analyze(markdown_doc, *args, **kwargs):
        calls.append(("analyze", markdown_doc))

    with (
        patch("doc_ai.cli.convert_path"),
        patch("doc_ai.cli.build_vector_store"),
        patch("doc_ai.cli.validate_doc", side_effect=fake_validate),
        patch("doc_ai.cli.analyze_doc", side_effect=fake_analyze),
    ):
        pipeline(src)

    assert calls == [
        ("validate", raw, md),
        ("analyze", md),
    ]


def test_pipeline_skips_non_raw_extensions(tmp_path):
    src = tmp_path / "docs"
    src.mkdir()
    raw = src / "sample.pdf"
    raw.write_text("raw")
    md = src / "sample.pdf.converted.md"
    md.write_text("converted")
    non_raw = src / "notes.txt"
    non_raw.write_text("text")

    calls = []

    def fake_validate(raw_file, rendered, *args, **kwargs):
        calls.append(("validate", raw_file, rendered))

    def fake_analyze(markdown_doc, *args, **kwargs):
        calls.append(("analyze", markdown_doc))

    with (
        patch("doc_ai.cli.convert_path"),
        patch("doc_ai.cli.build_vector_store"),
        patch("doc_ai.cli.validate_doc", side_effect=fake_validate),
        patch("doc_ai.cli.analyze_doc", side_effect=fake_analyze),
    ):
        pipeline(src)

    assert calls == [
        ("validate", raw, md),
        ("analyze", md),
    ]


def test_pipeline_ignores_converted_without_visiting(tmp_path):
    src = tmp_path / "docs"
    src.mkdir()
    raw = src / "sample.pdf"
    raw.write_text("raw")
    md = src / "sample.pdf.converted.md"
    md.write_text("converted")

    calls = []

    def fake_validate(raw_file, rendered, *args, **kwargs):
        calls.append(("validate", raw_file, rendered))

    def fake_analyze(markdown_doc, *args, **kwargs):
        calls.append(("analyze", markdown_doc))

    real_is_file = Path.is_file

    def spy_is_file(self: Path) -> bool:
        if self == md:
            raise AssertionError("converted output was visited")
        return real_is_file(self)

    with (
        patch("doc_ai.cli.convert_path"),
        patch("doc_ai.cli.build_vector_store"),
        patch("doc_ai.cli.validate_doc", side_effect=fake_validate),
        patch("doc_ai.cli.analyze_doc", side_effect=fake_analyze),
        patch.object(Path, "is_file", spy_is_file),
    ):
        pipeline(src)

    assert calls == [
        ("validate", raw, md),
        ("analyze", md),
    ]
