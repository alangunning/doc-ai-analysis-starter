from unittest.mock import patch

from typer.testing import CliRunner
from doc_ai.cli import app


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
        runner = CliRunner()
        result = runner.invoke(app, ["pipeline", str(src)])
        assert result.exit_code == 0

    assert calls == [
        ("validate", raw, md),
        ("analyze", md),
    ]
