import click
from pathlib import Path
from prompt_toolkit.history import FileHistory
from typer.main import get_command

from doc_ai.cli import app, interactive_shell


def test_interactive_shell_uses_click_repl(monkeypatch):
    called: dict[str, object] = {}

    def fake_repl(ctx, prompt=None, history=None, **_):  # type: ignore[no-redef]
        called["ctx"] = ctx
        called["prompt"] = prompt
        called["history"] = history

    monkeypatch.setattr("doc_ai.cli.interactive.repl", fake_repl)
    interactive_shell(app)

    assert callable(called["prompt"])
    assert called["prompt"]() == f"{Path.cwd().name}> "
    assert isinstance(called["history"], FileHistory)
    assert isinstance(called["ctx"], click.Context)
    assert called["ctx"].command.name == get_command(app).name
    assert "cd" in called["ctx"].command.commands

