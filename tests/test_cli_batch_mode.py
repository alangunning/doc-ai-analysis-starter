import click
from pathlib import Path
import pytest
import typer
from typer.main import get_command

from doc_ai.cli import app
from doc_ai.cli.interactive import run_batch


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
