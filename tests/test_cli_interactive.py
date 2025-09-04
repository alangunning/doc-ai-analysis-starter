import click
from typer.main import get_command

from doc_ai.cli import app, interactive_shell


def test_interactive_shell_uses_click_repl(monkeypatch):
    called: dict[str, object] = {}

    def fake_repl(ctx, prompt_kwargs=None, **_):  # type: ignore[no-redef]
        called["ctx"] = ctx
        called["prompt"] = prompt_kwargs

    monkeypatch.setattr("doc_ai.cli.interactive.repl", fake_repl)
    interactive_shell(app)

    assert called["prompt"] == {"message": "doc-ai> "}
    assert isinstance(called["ctx"], click.Context)
    assert called["ctx"].command.name == get_command(app).name

