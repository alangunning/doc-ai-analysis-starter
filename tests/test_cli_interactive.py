import os
import click
from pathlib import Path
from prompt_toolkit.history import FileHistory
from typer.main import get_command

from doc_ai.cli import app, interactive_shell
from doc_ai.cli.interactive import DocAICompleter, _prompt_name


def test_interactive_shell_uses_click_repl(tmp_path, monkeypatch):
    called: dict[str, object] = {}

    def fake_repl(ctx, prompt_kwargs=None, **_):  # type: ignore[no-redef]
        called["ctx"] = ctx
        called["prompt_kwargs"] = prompt_kwargs

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr("doc_ai.cli.interactive.repl", fake_repl)
    interactive_shell(app)

    pk = called["prompt_kwargs"]
    assert callable(pk["message"])
    assert pk["message"]() == f"{_prompt_name()}>"
    assert isinstance(pk["history"], FileHistory)
    history_path = Path(pk["history"].filename)
    assert history_path.parent == tmp_path / "doc_ai"
    assert history_path.parent.stat().st_mode & 0o777 == 0o700
    assert history_path.stat().st_mode & 0o777 == 0o600
    assert isinstance(pk["completer"], DocAICompleter)
    assert isinstance(called["ctx"], click.Context)
    assert called["ctx"].command.name == get_command(app).name
    assert "cd" in called["ctx"].command.commands


def test_prompt_updates_on_cd(tmp_path, monkeypatch):
    called: dict[str, object] = {}

    def fake_repl(ctx, prompt_kwargs=None, **_):  # type: ignore[no-redef]
        called["ctx"] = ctx
        called["prompt_kwargs"] = prompt_kwargs

    monkeypatch.setattr("doc_ai.cli.interactive.repl", fake_repl)
    interactive_shell(app)

    pk = called["prompt_kwargs"]
    ctx = called["ctx"]
    original_callable = pk["message"]

    start = Path.cwd()
    try:
        first = tmp_path / "one"
        first.mkdir()
        cmd = ctx.command
        sub = cmd.make_context(
            cmd.name, ["cd", str(first)], obj=ctx.obj, default_map=ctx.default_map
        )
        cmd.invoke(sub)
        ctx.default_map = sub.default_map
        ctx.obj = sub.obj
        assert pk["message"]() == f"{_prompt_name()}>"
        assert pk["message"] is not original_callable

        second = first / "two"
        second.mkdir()
        sub = cmd.make_context(
            cmd.name, ["cd", str(second)], obj=ctx.obj, default_map=ctx.default_map
        )
        cmd.invoke(sub)
        ctx.default_map = sub.default_map
        ctx.obj = sub.obj
        assert pk["message"]() == f"{_prompt_name()}>"
    finally:
        os.chdir(start)
