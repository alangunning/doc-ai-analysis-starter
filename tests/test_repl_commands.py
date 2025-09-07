import click
import pytest
from prompt_toolkit.history import FileHistory
from typer.main import get_command

import doc_ai.cli.interactive as interactive
from doc_ai import plugins
from doc_ai.batch import _parse_command
from doc_ai.cli import app
from doc_ai.cli.interactive import _register_repl_commands


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
    assert ":doc-types" in out
    assert ":topics" in out


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


def test_bang_executes_shell_command(capsys, monkeypatch):
    monkeypatch.setenv("DOC_AI_ALLOW_SHELL", "true")
    _setup()
    _parse_command("!python -c \"print('hi')\"")
    out = capsys.readouterr().out
    assert "hi" in out
    assert interactive.LAST_EXIT_CODE == 0


def test_bang_echo_still_works(capsys, monkeypatch):
    monkeypatch.setenv("DOC_AI_ALLOW_SHELL", "true")
    _setup()
    _parse_command("!echo hi")
    out = capsys.readouterr().out
    assert out.strip() == "hi"
    assert interactive.LAST_EXIT_CODE == 0


def test_bang_preserves_exit_status(capsys, monkeypatch):
    monkeypatch.setenv("DOC_AI_ALLOW_SHELL", "true")
    _setup()
    _parse_command('!python -c "import sys; sys.exit(3)"')
    capsys.readouterr()
    assert interactive.LAST_EXIT_CODE == 3


def test_bang_sanitizes_environment(monkeypatch, capsys):
    monkeypatch.setenv("DOC_AI_ALLOW_SHELL", "true")
    monkeypatch.delenv("DOC_AI_SAFE_ENV_VARS", raising=False)
    monkeypatch.setenv("SECRET_VAR", "topsecret")
    _setup()
    _parse_command("!env")
    out = capsys.readouterr().out
    assert "SECRET_VAR" not in out


def test_bang_allows_whitelisted_env(monkeypatch, capsys):
    monkeypatch.setenv("DOC_AI_ALLOW_SHELL", "true")
    monkeypatch.setenv("DOC_AI_SAFE_ENV_VARS", "PATH,HOME,SECRET_VAR")
    monkeypatch.setenv("SECRET_VAR", "revealed")
    _setup()
    _parse_command("!env")
    out = capsys.readouterr().out
    assert "SECRET_VAR=revealed" in out


def test_bang_warns_when_shell_disabled(monkeypatch):
    monkeypatch.delenv("DOC_AI_ALLOW_SHELL", raising=False)
    _setup()
    with pytest.warns(UserWarning, match="Shell escapes disabled"):
        _parse_command("!python -c \"print('hi')\"")
    assert interactive.LAST_EXIT_CODE == 1


def test_doc_types_and_topics_commands(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    (data_dir / "invoice").mkdir(parents=True)
    (data_dir / "invoice" / "analysis_sales.prompt.yaml").write_text("")
    (data_dir / "report").mkdir()
    (data_dir / "report" / "report.analysis.finance.prompt.yaml").write_text("")
    monkeypatch.chdir(tmp_path)
    _setup()
    _parse_command(":doc-types")
    out = capsys.readouterr().out.splitlines()
    assert {"invoice", "report"} <= set(out)
    _parse_command(":topics")
    out = capsys.readouterr().out.splitlines()
    assert {"sales", "finance"} <= set(out)


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


def test_edit_prompt_external_editor(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "invoice"
    data_dir.mkdir(parents=True)
    prompt = data_dir / "invoice.analysis.prompt.yaml"
    prompt.write_text("old")
    monkeypatch.chdir(tmp_path)
    _setup()
    captured: dict[str, str] = {}

    def fake_edit(text: str) -> str:
        captured["text"] = text
        return "new text"

    monkeypatch.setattr(click, "edit", fake_edit)
    _parse_command(":edit-prompt invoice")
    assert captured["text"].strip() == "old"
    assert prompt.read_text() == "new text\n"


def test_edit_url_list_external_editor(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "invoice"
    data_dir.mkdir(parents=True)
    urls_file = data_dir / "urls.txt"
    urls_file.write_text("http://a.com\n")
    monkeypatch.chdir(tmp_path)
    _setup()
    edited = "http://b.com\ninvalid\nhttp://a.com\n"
    captured: dict[str, str] = {}

    def fake_edit(text: str) -> str:
        captured["text"] = text
        return edited

    monkeypatch.setattr(click, "edit", fake_edit)
    called: list[bool] = []
    monkeypatch.setattr(interactive, "refresh_completer", lambda: called.append(True))
    _parse_command(":edit-url-list invoice")
    assert captured["text"].strip() == "http://a.com"
    assert urls_file.read_text() == "http://b.com\nhttp://a.com\n"
    assert called
