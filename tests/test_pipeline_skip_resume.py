from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from doc_ai.cli import app


def _setup_docs(tmp_path: Path) -> Path:
    src = tmp_path / "docs"
    src.mkdir()
    raw = src / "sample.pdf"
    raw.write_text("raw")
    md = src / "sample.pdf.converted.md"
    md.write_text("converted")
    return src


def test_pipeline_cli_resume_and_skip(tmp_path):
    src = _setup_docs(tmp_path)
    calls: list[str] = []

    def recorder(step: str):
        def _inner(*args, **kwargs):
            calls.append(step)

        return _inner

    with (
        patch("doc_ai.cli.convert_path", side_effect=recorder("convert")),
        patch("doc_ai.cli.validate_doc", side_effect=recorder("validate")),
        patch("doc_ai.cli.analyze_doc", side_effect=recorder("analyze")),
        patch("doc_ai.cli.build_vector_store", side_effect=recorder("embed")),
    ):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "pipeline",
                "--resume-from",
                "validate",
                "--skip",
                "analyze",
                str(src),
            ],
        )

    assert result.exit_code == 0, result.stdout
    assert calls == ["validate", "embed"]
