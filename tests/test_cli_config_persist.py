from pathlib import Path
import os
import importlib

from dotenv import load_dotenv
from typer.testing import CliRunner


def test_config_persists_to_env_file(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        monkeypatch.setattr(cli, "find_dotenv", lambda *a, **k: ".env")
        result = runner.invoke(cli.app, ["config", "--set", "FOO=bar"])
        assert result.exit_code == 0
        assert Path(".env").read_text().strip() == "FOO=bar"
        os.environ.pop("FOO", None)
        load_dotenv(Path(".env"), override=True)
        assert os.getenv("FOO") == "bar"
        os.environ.pop("FOO", None)

