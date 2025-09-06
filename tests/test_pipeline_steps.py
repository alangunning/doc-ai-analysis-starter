import importlib
from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from doc_ai.cli import pipeline
from doc_ai.cli.pipeline import PipelineStep

pipeline_module = importlib.import_module("doc_ai.cli.pipeline")


def _setup_docs(tmp_path: Path) -> tuple[Path, Path, Path]:
    src = tmp_path / "docs"
    src.mkdir()
    raw = src / "sample.pdf"
    raw.write_text("raw")
    md = src / "sample.pdf.converted.md"
    md.write_text("converted")
    return src, raw, md


def test_pipeline_resume_from_validate_skips_convert(tmp_path):
    src, raw, md = _setup_docs(tmp_path)
    calls = []

    def fake_validate(raw_file, rendered, *args, **kwargs):
        calls.append(("validate", raw_file, rendered))

    def fake_analyze(markdown_doc, *args, **kwargs):
        calls.append(("analyze", markdown_doc))

    with (
        patch("doc_ai.cli.convert_path") as convert_mock,
        patch("doc_ai.cli.build_vector_store"),
        patch("doc_ai.cli.validate_doc", side_effect=fake_validate),
        patch("doc_ai.cli.analyze_doc", side_effect=fake_analyze),
    ):
        pipeline(src, resume_from=PipelineStep.VALIDATE)

    convert_mock.assert_not_called()
    assert calls == [("validate", raw, md), ("analyze", md)]


def test_pipeline_skip_validate(tmp_path):
    src, raw, md = _setup_docs(tmp_path)
    calls = []

    def fake_analyze(markdown_doc, *args, **kwargs):
        calls.append(("analyze", markdown_doc))

    with (
        patch("doc_ai.cli.convert_path") as convert_mock,
        patch("doc_ai.cli.build_vector_store"),
        patch("doc_ai.cli.validate_doc") as validate_mock,
        patch("doc_ai.cli.analyze_doc", side_effect=fake_analyze),
    ):
        pipeline(src, skip=[PipelineStep.VALIDATE])

    validate_mock.assert_not_called()
    convert_mock.assert_called_once()
    assert calls == [("analyze", md)]


def test_pipeline_handles_unexpected_error(tmp_path, monkeypatch):
    src, raw, md = _setup_docs(tmp_path)

    def boom(*args, **kwargs):  # pragma: no cover - testing error path
        raise RuntimeError("boom")

    messages: list[str] = []

    def fake_error(msg, *args, **kwargs):
        messages.append(msg % args)

    monkeypatch.setattr("doc_ai.cli.convert_path", boom)
    monkeypatch.setattr(pipeline_module.logger, "error", fake_error)

    with pytest.raises(typer.Exit) as excinfo:
        pipeline(src)
    assert excinfo.value.exit_code == 1
    assert any("Conversion failed" in m for m in messages)
