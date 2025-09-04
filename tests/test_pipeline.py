from pathlib import Path

from typer.testing import CliRunner

from doc_ai.cli import app


def _setup_docs(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    for name in ["a.pdf", "b.pdf"]:
        (src / name).touch()
        (src / f"{name}.converted.md").touch()
    return src


def test_pipeline_keep_going_reports_failures(monkeypatch, tmp_path):
    src = _setup_docs(tmp_path)
    calls: list[str] = []

    def fake_validate(raw, md, fmt, prompt, model, base_url):
        calls.append(f"validate:{Path(raw).name}")
        if Path(raw).name == "b.pdf":
            raise RuntimeError("boom")

    def fake_analyze(md, **kwargs):
        calls.append(f"analyze:{Path(md).name}")
        if Path(md).name == "b.pdf.converted.md":
            raise ValueError("kaboom")

    monkeypatch.setattr("doc_ai.cli.validate_doc", fake_validate)
    monkeypatch.setattr("doc_ai.cli.analyze_doc", fake_analyze)
    monkeypatch.setattr("doc_ai.cli.convert_path", lambda *a, **k: None)
    monkeypatch.setattr("doc_ai.cli.build_vector_store", lambda *a, **k: None)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "--keep-going", str(src)])

    assert result.exit_code == 1
    assert "Validation failed" in result.stdout
    assert "Analysis failed" in result.stdout
    assert "Failures encountered" in result.stdout
    assert sorted(calls) == sorted([
        "validate:a.pdf",
        "analyze:a.pdf.converted.md",
        "validate:b.pdf",
        "analyze:b.pdf.converted.md",
    ])


def test_pipeline_fail_fast_stops(monkeypatch, tmp_path):
    src = _setup_docs(tmp_path)
    calls: list[str] = []

    def fake_validate(raw, md, fmt, prompt, model, base_url):
        calls.append(f"validate:{Path(raw).name}")
        raise RuntimeError("boom")

    def fake_analyze(md, **kwargs):
        calls.append(f"analyze:{Path(md).name}")

    monkeypatch.setattr("doc_ai.cli.validate_doc", fake_validate)
    monkeypatch.setattr("doc_ai.cli.analyze_doc", fake_analyze)
    monkeypatch.setattr("doc_ai.cli.convert_path", lambda *a, **k: None)
    monkeypatch.setattr("doc_ai.cli.build_vector_store", lambda *a, **k: None)

    runner = CliRunner()
    result = runner.invoke(app, ["pipeline", "--fail-fast", str(src)])

    assert result.exit_code == 1
    assert "Validation failed" in result.stdout
    assert len(calls) == 1 and calls[0].startswith("validate:")
