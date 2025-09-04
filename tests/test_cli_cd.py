from pathlib import Path
import os

import click
from typer.testing import CliRunner
from typer.main import get_command

from doc_ai.cli import app
import doc_ai.cli as cli_module
from doc_ai.cli import config as config_module


def test_cd_changes_directory(tmp_path):
    runner = CliRunner()
    original = Path.cwd()
    target = tmp_path / "subdir"
    target.mkdir()
    result = runner.invoke(app, ["cd", str(target)])
    assert result.exit_code == 0
    try:
        assert Path.cwd() == target
    finally:
        os.chdir(original)


def test_cd_refreshes_config_for_multi_project_session(tmp_path):
    project_one = tmp_path / "one"
    project_two = tmp_path / "two"
    project_one.mkdir()
    project_two.mkdir()
    (project_one / ".env").write_text("FOO=one\n")
    (project_two / ".env").write_text("FOO=two\n")

    original = Path.cwd()
    prev = os.environ.pop("FOO", None)
    original_env_file = cli_module.ENV_FILE
    try:
        cmd = get_command(app)
        ctx = click.Context(cmd, obj={})

        sub = cmd.make_context(
            cmd.name, ["cd", str(project_one)], obj=ctx.obj, default_map=ctx.default_map
        )
        cmd.invoke(sub)
        ctx.default_map = sub.default_map
        ctx.obj = sub.obj
        assert ctx.obj["config"]["FOO"] == "one"
        assert os.getenv("FOO") == "one"

        sub = cmd.make_context(
            cmd.name, ["cd", str(project_two)], obj=ctx.obj, default_map=ctx.default_map
        )
        cmd.invoke(sub)
        ctx.default_map = sub.default_map
        ctx.obj = sub.obj
        assert ctx.obj["config"]["FOO"] == "two"
        assert os.getenv("FOO") == "two"
    finally:
        os.chdir(original)
        if prev is not None:
            os.environ["FOO"] = prev
        elif "FOO" in os.environ:
            del os.environ["FOO"]
        cli_module.ENV_FILE = original_env_file
        config_module.ENV_FILE = original_env_file
