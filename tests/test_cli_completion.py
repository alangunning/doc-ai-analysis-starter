from typer.testing import CliRunner
from prompt_toolkit.document import Document

import importlib
import click
from doc_ai.cli.interactive import DocAICompleter
from typer.main import get_command


def test_show_completion():
    import doc_ai.cli as cli_mod

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.app,
        ["--show-completion"],
        env={"SHELL": "/bin/bash"},
        prog_name="doc-ai",
    )
    assert result.exit_code == 0
    assert "_DOC_AI_COMPLETE=complete_bash" in result.stdout


def test_completer_hides_sensitive_env(tmp_path, monkeypatch):
    import doc_ai.cli as cli_mod

    monkeypatch.setenv("PATH", "/bin")
    monkeypatch.setenv("MY_SECRET", "x")
    monkeypatch.setenv("MY_API_KEY", "x")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_DIR", tmp_path)
    importlib.reload(cli_mod)
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_DIR", tmp_path)
    cmd = get_command(cli_mod.app)
    ctx = click.Context(cmd)
    comp = DocAICompleter(cmd, ctx)
    completions = list(comp.get_completions(Document("$"), None))
    texts = {c.text for c in completions}
    assert "$PATH" in texts
    assert "$MY_SECRET" not in texts
    assert "$MY_API_KEY" not in texts


def test_completer_allows_whitelisted_env(tmp_path, monkeypatch):
    import doc_ai.cli as cli_mod

    monkeypatch.setenv("MY_API_KEY", "x")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_DIR", tmp_path)
    importlib.reload(cli_mod)
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_DIR", tmp_path)
    cmd = get_command(cli_mod.app)
    ctx = click.Context(cmd, obj={"config": {"DOC_AI_SAFE_ENV_VARS": "MY_API_KEY"}})
    comp = DocAICompleter(cmd, ctx)
    completions = list(comp.get_completions(Document("$"), None))
    texts = {c.text for c in completions}
    assert "$MY_API_KEY" in texts


def test_completer_blocks_blacklisted_env(tmp_path, monkeypatch):
    import doc_ai.cli as cli_mod

    monkeypatch.setenv("VISIBLE", "1")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_DIR", tmp_path)
    importlib.reload(cli_mod)
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_DIR", tmp_path)
    cmd = get_command(cli_mod.app)
    ctx = click.Context(
        cmd, obj={"config": {"DOC_AI_SAFE_ENV_VARS": "VISIBLE,-VISIBLE"}}
    )
    comp = DocAICompleter(cmd, ctx)
    completions = list(comp.get_completions(Document("$"), None))
    texts = {c.text for c in completions}
    assert "$VISIBLE" not in texts


def test_completer_respects_env_var_allowlist(tmp_path, monkeypatch):
    import doc_ai.cli as cli_mod

    monkeypatch.setenv("MY_API_KEY", "x")
    monkeypatch.setenv("SECRET_TOKEN", "y")
    monkeypatch.setenv("DOC_AI_SAFE_ENV_VARS", "MY_API_KEY")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_DIR", tmp_path)
    importlib.reload(cli_mod)
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_DIR", tmp_path)
    cmd = get_command(cli_mod.app)
    ctx = click.Context(cmd)
    comp = DocAICompleter(cmd, ctx)
    completions = {c.text for c in comp.get_completions(Document("$"), None)}
    assert "$MY_API_KEY" in completions
    assert "$SECRET_TOKEN" not in completions


def test_safe_env_config_updates_completion(tmp_path, monkeypatch):
    import doc_ai.cli as cli_mod

    monkeypatch.setenv("MY_API_KEY", "x")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_DIR", tmp_path)
    importlib.reload(cli_mod)
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(cli_mod, "GLOBAL_CONFIG_DIR", tmp_path)

    cmd = get_command(cli_mod.app)
    ctx = click.Context(cmd)
    comp = DocAICompleter(cmd, ctx)
    completions = {c.text for c in comp.get_completions(Document("$"), None)}
    assert "$MY_API_KEY" not in completions

    runner = CliRunner()
    result = runner.invoke(cli_mod.app, ["config", "safe-env", "add", "MY_API_KEY"])
    assert result.exit_code == 0

    comp.refresh()
    completions = {c.text for c in comp.get_completions(Document("$"), None)}
    assert "$MY_API_KEY" in completions


def test_completer_suggests_doc_types_and_topics(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    (data_dir / "invoice").mkdir(parents=True)
    (data_dir / "invoice" / "analysis_sales.prompt.yaml").write_text("")
    (data_dir / "report").mkdir()
    (data_dir / "report" / "report.analysis.finance.prompt.yaml").write_text("")
    monkeypatch.chdir(tmp_path)
    import doc_ai.cli as cli_mod

    cmd = get_command(cli_mod.app)
    ctx = click.Context(cmd)
    comp = DocAICompleter(cmd, ctx)

    doc_completions = list(comp.get_completions(Document("pipeline "), None))
    docs = {c.text for c in doc_completions}
    assert {"invoice", "report"} <= docs

    topic_completions = list(comp.get_completions(Document("analyze --topic "), None))
    topics = {c.text for c in topic_completions}
    assert {"sales", "finance"} <= topics


def test_completer_suggests_urls_doc_types(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    (data_dir / "alpha").mkdir(parents=True)
    (data_dir / "beta").mkdir()
    monkeypatch.chdir(tmp_path)
    import doc_ai.cli as cli_mod

    cmd = get_command(cli_mod.app)
    ctx = click.Context(cmd)
    comp = DocAICompleter(cmd, ctx)

    completions = list(comp.get_completions(Document("urls "), None))
    texts = {c.text for c in completions}
    assert {"alpha", "beta"} <= texts
