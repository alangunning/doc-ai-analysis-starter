from pathlib import Path

from typer.testing import CliRunner

from doc_ai.cli import app
import importlib
pipeline_module = importlib.import_module("doc_ai.cli.pipeline")
from doc_ai.cli.pipeline import pipeline as run_pipeline


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

    def fake_validate(raw, md, fmt, prompt, model, base_url, **kwargs):
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

    def fake_validate(raw, md, fmt, prompt, model, base_url, **kwargs):
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


def test_pipeline_workers_option(monkeypatch, tmp_path):
    src = _setup_docs(tmp_path)
    captured: dict[str, int] = {}

    class DummyExecutor:
        def __init__(self, max_workers):
            captured['max_workers'] = max_workers

        def submit(self, fn, *args, **kwargs):
            fn(*args, **kwargs)

            class DummyFuture:
                def result(self):
                    pass

            return DummyFuture()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(pipeline_module, "ThreadPoolExecutor", DummyExecutor)
    monkeypatch.setattr("doc_ai.cli.convert_path", lambda *a, **k: None)
    monkeypatch.setattr("doc_ai.cli.validate_doc", lambda *a, **k: None)
    monkeypatch.setattr("doc_ai.cli.analyze_doc", lambda *a, **k: None)
    monkeypatch.setattr("doc_ai.cli.build_vector_store", lambda *a, **k: None)

    run_pipeline(src, workers=3)
    assert captured['max_workers'] == 3
