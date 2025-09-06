import logging

import click
import pytest
import typer
from typer.main import get_command

from doc_ai.batch import run_batch
from doc_ai.cli import app, interactive_shell


def test_run_batch_sets_defaults(tmp_path):
    init = tmp_path / "init.txt"
    init.write_text("set model=gpt-4o\n")
    cmd = get_command(app)
    ctx = click.Context(cmd)
    run_batch(ctx, init)
    assert ctx.default_map["model"] == "gpt-4o"


def test_run_batch_propagates_exit(tmp_path):
    init = tmp_path / "init.txt"
    init.write_text("cd does-not-exist\n")
    cmd = get_command(app)
    ctx = click.Context(cmd)
    with pytest.raises(typer.Exit):
        run_batch(ctx, init)


def test_run_batch_reports_parse_error(tmp_path):
    init = tmp_path / "init.txt"
    init.write_text("add url 'unterminated\n")
    cmd = get_command(app)
    ctx = click.Context(cmd)
    with pytest.raises(click.ClickException) as excinfo:
        run_batch(ctx, init)
    assert str(init) in str(excinfo.value)


def test_repl_starts_after_batch_error(tmp_path, monkeypatch, caplog):
    init = tmp_path / "init.txt"
    init.write_text("boguscmd\n")
    called: dict[str, object] = {}

    def fake_repl(ctx, prompt_kwargs=None, **_):  # type: ignore[no-redef]
        called["ctx"] = ctx

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr("doc_ai.cli.interactive.repl", fake_repl)
    with caplog.at_level(logging.ERROR, logger="doc_ai.cli.interactive"):
        interactive_shell(app, init=init)

    assert "ctx" in called
    assert "Failed to run batch file" in caplog.text
