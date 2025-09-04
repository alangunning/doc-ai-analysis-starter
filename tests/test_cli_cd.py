from pathlib import Path
import os

from typer.testing import CliRunner

from doc_ai.cli import app


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
