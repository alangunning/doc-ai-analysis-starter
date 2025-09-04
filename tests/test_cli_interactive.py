import click
from pathlib import Path
from prompt_toolkit.history import FileHistory
from typer.main import get_command

from doc_ai.cli import app, interactive_shell
from doc_ai.cli.interactive import DocAICompleter


def test_interactive_shell_uses_click_repl(monkeypatch):
    called: dict[str, object] = {}

    def fake_repl(ctx, prompt_kwargs=None, **_):  # type: ignore[no-redef]
        called["ctx"] = ctx
        called["prompt_kwargs"] = prompt_kwargs

    monkeypatch.setattr("doc_ai.cli.interactive.repl", fake_repl)
    interactive_shell(app)

    pk = called["prompt_kwargs"]
    assert pk["message"] == "doc-ai>"
    assert isinstance(pk["history"], FileHistory)
    assert isinstance(pk["completer"], DocAICompleter)
    assert isinstance(called["ctx"], click.Context)
    assert called["ctx"].command.name == get_command(app).name
    assert "cd" in called["ctx"].command.commands

