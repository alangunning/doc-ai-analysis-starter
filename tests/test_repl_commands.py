import click
from prompt_toolkit.history import FileHistory
from typer.main import get_command

from doc_ai.cli import app
import doc_ai.cli.interactive as interactive
from doc_ai.cli.interactive import _register_repl_commands
from doc_ai.batch import _parse_command
from doc_ai import plugins


def _setup():
    plugins._reset()
    ctx = click.Context(get_command(app))
    _register_repl_commands(ctx)


def test_help_lists_repl_commands(capsys):
    _setup()
    interactive._repl_help([])
    out = capsys.readouterr().out
    assert ":new-doc-type" in out
    assert ":manage-urls" in out


def test_help_lists_subcommands(capsys):
    _setup()
    _parse_command(":help add")
    out = capsys.readouterr().out
    assert "Subcommands:" in out
    assert "url" in out
    assert "Example:" in out


def test_reload_triggers_refresh(monkeypatch):
    _setup()
    called = []
    monkeypatch.setattr(interactive, "refresh_completer", lambda: called.append(True))
    _parse_command(":reload")
    assert called


def test_history_outputs_entries(tmp_path, capsys):
    _setup()
    hist = FileHistory(str(tmp_path / "history"))
    hist.append_string("first")
    hist.append_string("second")
    interactive.PROMPT_KWARGS = {"history": hist}
    _parse_command(":history")
    out = capsys.readouterr().out
    assert "1: first" in out
    assert "2: second" in out


def test_chmod_failure_is_handled(monkeypatch, tmp_path):
    plugins._reset()
    monkeypatch.setattr(
        interactive.os,
        "chmod",
        lambda *a, **k: (_ for _ in ()).throw(OSError("boom")),
    )

    class DummyDirs:
        def __init__(self, *a, **k):
            self.user_data_path = tmp_path

    monkeypatch.setattr(interactive, "PlatformDirs", DummyDirs)
    monkeypatch.setattr(interactive, "repl", lambda *a, **k: None)
    interactive.interactive_shell(app)
    assert (tmp_path / "history").exists()
