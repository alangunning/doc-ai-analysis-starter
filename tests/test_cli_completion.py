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
    monkeypatch.setenv("DOC_AI_SAFE_ENV_VARS", "MY_API_KEY")
    cmd = get_command(app)
    ctx = click.Context(cmd)
    comp = DocAICompleter(cmd, ctx)
    completions = list(comp.get_completions(Document("$"), None))
    texts = {c.text for c in completions}
    assert "$MY_API_KEY" in texts
