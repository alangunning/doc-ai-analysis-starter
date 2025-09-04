from pathlib import Path
import importlib

from typer.testing import CliRunner


def test_config_creates_env_with_strict_permissions(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        monkeypatch.setattr(cli, "ENV_FILE", ".env")
        result = runner.invoke(cli.app, ["config", "--set", "FOO=bar"])
        assert result.exit_code == 0
        env_path = Path(".env")
        assert env_path.exists()
        assert env_path.stat().st_mode & 0o777 == 0o600
