import importlib
from pathlib import Path

from typer.testing import CliRunner


def test_env_overrides_builtin_pipeline_workers(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        src = Path("docs")
        src.mkdir()
        (src / "a.pdf").write_text("raw")
        prompt_dir = Path(".github/prompts")
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "doc-analysis.analysis.prompt.yaml").write_text("prompt")
        monkeypatch.setenv("WORKERS", "3")
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        pipeline_mod = cli.pipeline_cmd

        called = {}

        def fake_pipeline(
            source,
            prompt,
            format,
            model,
            base_model_url,
            fail_fast,
            show_cost,
            estimate,
            workers,
            force,
            dry_run,
            resume_from,
            skip,
        ):
            called["workers"] = workers

        monkeypatch.setattr(pipeline_mod, "pipeline", fake_pipeline)
        result = runner.invoke(cli.app, ["pipeline", "--dry-run", "docs"])
        assert result.exit_code == 0
        assert called["workers"] == 3


def test_env_file_overrides_builtin_analyze_show_cost(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("report.converted.md").write_text("doc")
        Path(".env").write_text("SHOW_COST=true\n")
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        analyze_mod = importlib.reload(importlib.import_module("doc_ai.cli.analyze"))

        called = {}

        def fake_analyze_doc(*args, **kwargs):
            called["show_cost"] = args[6]

        monkeypatch.setattr(analyze_mod, "analyze_doc", fake_analyze_doc)
        result = runner.invoke(cli.app, ["analyze", "report.converted.md"])
        assert result.exit_code == 0
        assert called["show_cost"] is True
