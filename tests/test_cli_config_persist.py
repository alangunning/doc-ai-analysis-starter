from pathlib import Path
import os
import importlib
import json

from dotenv import load_dotenv
from typer.testing import CliRunner


def test_config_persists_to_env_file(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        monkeypatch.setenv("XDG_CONFIG_HOME", str(Path(".")))
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        monkeypatch.setattr(cli, "ENV_FILE", ".env")
        result = runner.invoke(cli.app, ["config", "--set", "FOO=bar", "--project"])
        assert result.exit_code == 0
        env_path = Path(".env")
        assert env_path.read_text().strip() == "FOO=bar"
        assert env_path.stat().st_mode & 0o777 == 0o600
        config_path = Path("doc_ai/config.json")
        data = json.loads(config_path.read_text())
        assert data["FOO"] == "bar"
        os.environ.pop("FOO", None)
        load_dotenv(env_path, override=True)
        assert os.getenv("FOO") == "bar"
        os.environ.pop("FOO", None)
        # Update again to ensure permissions persist through set_key
        result = runner.invoke(cli.app, ["config", "--set", "BAZ=qux", "--project"])
        assert result.exit_code == 0
        assert env_path.stat().st_mode & 0o777 == 0o600
        lines = env_path.read_text().strip().splitlines()
        assert "FOO=bar" in lines and "BAZ=qux" in lines
        data = json.loads(config_path.read_text())
        assert data["BAZ"] == "qux"

