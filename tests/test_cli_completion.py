from typer.testing import CliRunner
from prompt_toolkit.document import Document

from doc_ai.cli import app
from doc_ai.cli.interactive import DocAICompleter
import click
from typer.main import get_command


def test_show_completion():
    runner = CliRunner()
    result = runner.invoke(
        app, ["--show-completion"], env={"SHELL": "/bin/bash"}, prog_name="doc-ai"
    )
    assert result.exit_code == 0
    assert "_DOC_AI_COMPLETE=complete_bash" in result.stdout


def test_completer_hides_sensitive_env(monkeypatch):
    monkeypatch.setenv("VISIBLE", "1")
    monkeypatch.setenv("MY_SECRET", "x")
    monkeypatch.setenv("MY_API_KEY", "x")
    cmd = get_command(app)
    ctx = click.Context(cmd)
    comp = DocAICompleter(cmd, ctx)
    completions = list(comp.get_completions(Document("$"), None))
    texts = {c.text for c in completions}
    assert "$VISIBLE" in texts
    assert "$MY_SECRET" not in texts
    assert "$MY_API_KEY" not in texts


def test_completer_allows_whitelisted_env(monkeypatch):
    monkeypatch.setenv("MY_API_KEY", "x")
    cmd = get_command(app)
    ctx = click.Context(cmd, obj={"config": {"DOC_AI_SAFE_ENV_VARS": "MY_API_KEY"}})
    comp = DocAICompleter(cmd, ctx)
    completions = list(comp.get_completions(Document("$"), None))
    texts = {c.text for c in completions}
    assert "$MY_API_KEY" in texts


def test_completer_blocks_blacklisted_env(monkeypatch):
    monkeypatch.setenv("VISIBLE", "1")
    cmd = get_command(app)
    ctx = click.Context(cmd, obj={"config": {"DOC_AI_SAFE_ENV_VARS": "-VISIBLE"}})
    comp = DocAICompleter(cmd, ctx)
    completions = list(comp.get_completions(Document("$"), None))
    texts = {c.text for c in completions}
    assert "$VISIBLE" not in texts


def test_completer_suggests_doc_types_and_topics(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    (data_dir / "invoice").mkdir(parents=True)
    (data_dir / "invoice" / "analysis_sales.prompt.yaml").write_text("")
    (data_dir / "report").mkdir()
    (data_dir / "report" / "report.analysis.finance.prompt.yaml").write_text("")
    monkeypatch.chdir(tmp_path)
    cmd = get_command(app)
    ctx = click.Context(cmd)
    comp = DocAICompleter(cmd, ctx)

    doc_completions = list(comp.get_completions(Document("pipeline "), None))
    docs = {c.text for c in doc_completions}
    assert {"invoice", "report"} <= docs

    topic_completions = list(comp.get_completions(Document("analyze --topic "), None))
    topics = {c.text for c in topic_completions}
    assert {"sales", "finance"} <= topics


def test_completer_suggests_manage_urls_doc_types(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    (data_dir / "alpha").mkdir(parents=True)
    (data_dir / "beta").mkdir()
    monkeypatch.chdir(tmp_path)
    cmd = get_command(app)
    ctx = click.Context(cmd)
    comp = DocAICompleter(cmd, ctx)

    completions = list(comp.get_completions(Document("add manage-urls "), None))
    texts = {c.text for c in completions}
    assert {"alpha", "beta"} <= texts
