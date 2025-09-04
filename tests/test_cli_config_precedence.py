import importlib
import json
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


def test_env_overrides_pipeline_resume_from(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        src = Path("docs")
        src.mkdir()
        (src / "a.pdf").write_text("raw")
        prompt_dir = Path(".github/prompts")
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "doc-analysis.analysis.prompt.yaml").write_text("prompt")
        monkeypatch.setenv("RESUME_FROM", "analyze")
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
            called["resume_from"] = resume_from

        monkeypatch.setattr(pipeline_mod, "pipeline", fake_pipeline)
        result = runner.invoke(cli.app, ["pipeline", "--dry-run", "docs"])
        assert result.exit_code == 0
        assert called["resume_from"] == pipeline_mod.PipelineStep.ANALYZE


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


def test_env_overrides_embed_fail_fast(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        src = Path("docs")
        src.mkdir()
        monkeypatch.setenv("FAIL_FAST", "true")
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        embed_mod = importlib.reload(importlib.import_module("doc_ai.cli.embed"))

        called = {}

        def fake_build_vector_store(source, fail_fast=False, workers=1):
            called["fail_fast"] = fail_fast

        monkeypatch.setattr(embed_mod, "build_vector_store", fake_build_vector_store)
        result = runner.invoke(cli.app, ["embed", "docs"])
        assert result.exit_code == 0
        assert called["fail_fast"] is True


def test_env_file_overrides_validate_force(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("doc.pdf").write_text("raw")
        Path("doc.pdf.converted.md").write_text("md")
        Path(".env").write_text("FORCE=true\n")
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        validate_mod = importlib.reload(importlib.import_module("doc_ai.cli.validate"))

        called = {}

        def fake_validate_doc(
            raw,
            rendered,
            fmt,
            prompt,
            model,
            base_model_url,
            *,
            show_progress=False,
            logger=None,
            console=None,
            validate_file_func=None,
            force=False,
        ):
            called["force"] = force

        monkeypatch.setattr(validate_mod, "validate_doc", fake_validate_doc)
        result = runner.invoke(cli.app, ["validate", "doc.pdf"])
        assert result.exit_code == 0
        assert called["force"] is True


def test_env_overrides_query_ask(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        store = Path("emb")
        store.mkdir()
        (store / "doc.embedding.json").write_text(
            json.dumps({"embedding": [0.1, 0.2], "file": "doc.txt"})
        )
        monkeypatch.setenv("ASK", "true")
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        query_mod = importlib.reload(importlib.import_module("doc_ai.cli.query"))

        class FakeEmbeddingsClient:
            def create(self, model, input, encoding_format):
                class Data:
                    embedding = [0.1, 0.2]

                class Resp:
                    data = [Data()]

                return Resp()

        class FakeClient:
            embeddings = FakeEmbeddingsClient()

        monkeypatch.setattr(query_mod, "OpenAI", lambda api_key, base_url: FakeClient())

        called = {}

        def fake_create_response(client, model, texts):
            called["used"] = True

            class Resp:
                output_text = ""

            return Resp()

        monkeypatch.setattr(query_mod, "create_response", fake_create_response)
        result = runner.invoke(cli.app, ["query", "emb", "hello"])
        assert result.exit_code == 0
        assert called.get("used") is True


def test_env_overrides_init_workflows_dest(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        monkeypatch.setenv("DEST", "wf")
        monkeypatch.setenv("DRY_RUN", "true")
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        init_mod = importlib.reload(importlib.import_module("doc_ai.cli.init_workflows"))

        copied = {"called": False}

        def fake_copy2(src, dst):
            copied["called"] = True

        monkeypatch.setattr(init_mod.shutil, "copy2", fake_copy2)
        result = runner.invoke(cli.app, ["init-workflows"])
        assert result.exit_code == 0
        assert Path("wf").exists()
        assert not Path(".github/workflows").exists()
        assert copied["called"] is False


def test_global_config_used_without_env(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        monkeypatch.delenv("FAIL_FAST", raising=False)
        src = Path("docs")
        src.mkdir()
        global_cfg = Path("config.json")
        global_cfg.write_text(json.dumps({"FAIL_FAST": True}))
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        monkeypatch.setattr(cli, "GLOBAL_CONFIG_PATH", global_cfg)
        embed_mod = importlib.reload(importlib.import_module("doc_ai.cli.embed"))

        called = {}

        def fake_build_vector_store(source, fail_fast=False, workers=1):
            called["fail_fast"] = fail_fast

        monkeypatch.setattr(embed_mod, "build_vector_store", fake_build_vector_store)
        result = runner.invoke(cli.app, ["embed", "docs"])
        assert result.exit_code == 0
        assert called["fail_fast"] is True


def test_project_env_overrides_global_config(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        monkeypatch.delenv("FAIL_FAST", raising=False)
        src = Path("docs")
        src.mkdir()
        global_cfg = Path("config.json")
        global_cfg.write_text(json.dumps({"FAIL_FAST": True}))
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        monkeypatch.setattr(cli, "GLOBAL_CONFIG_PATH", global_cfg)
        Path(".env").write_text("FAIL_FAST=false\n")
        embed_mod = importlib.reload(importlib.import_module("doc_ai.cli.embed"))

        called = {}

        def fake_build_vector_store(source, fail_fast=False, workers=1):
            called["fail_fast"] = fail_fast

        monkeypatch.setattr(embed_mod, "build_vector_store", fake_build_vector_store)
        result = runner.invoke(cli.app, ["embed", "docs"])
        assert result.exit_code == 0
        assert called["fail_fast"] is False


def test_config_set_parses_bool_and_validates(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        monkeypatch.delenv("FAIL_FAST", raising=False)
        config_mod = importlib.reload(importlib.import_module("doc_ai.cli.config"))
        saved = {}
        monkeypatch.setattr(config_mod, "save_global_config", lambda c: saved.update(c))
        monkeypatch.setattr(config_mod, "read_configs", lambda: ({}, {}, {}))
        result = runner.invoke(config_mod.app, ["set", "--global", "FAIL_FAST=true"])
        assert result.exit_code == 0
        assert saved["FAIL_FAST"] is True
        result = runner.invoke(config_mod.app, ["set", "--global", "UNKNOWN=true"])
        assert result.exit_code != 0


def test_config_toggle(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        monkeypatch.delenv("FAIL_FAST", raising=False)
        config_mod = importlib.reload(importlib.import_module("doc_ai.cli.config"))
        saved = {}
        monkeypatch.setattr(config_mod, "save_global_config", lambda c: saved.update(c))
        monkeypatch.setattr(config_mod, "read_configs", lambda: ({}, {}, {}))
        result = runner.invoke(config_mod.app, ["toggle", "--global", "FAIL_FAST"])
        assert result.exit_code == 0
        assert saved["FAIL_FAST"] is True
        result = runner.invoke(config_mod.app, ["toggle", "--global", "FAIL_FAST"])
        assert result.exit_code == 0
        assert saved["FAIL_FAST"] is False
