import json
import re
import importlib
from pathlib import Path

from typer.testing import CliRunner


def _parse_line(stdout: str, var: str) -> list[str]:
    for line in stdout.splitlines():
        clean = line.replace("│", " ").strip()
        if clean.startswith(var + " "):
            return re.split(r"\s{2,}", clean)
    raise AssertionError(f"{var} not found")


def test_global_config_precedence(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        monkeypatch.setenv("XDG_CONFIG_HOME", str(Path("xdg")))
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        monkeypatch.setattr(cli, "ENV_FILE", ".env")

        result = runner.invoke(cli.app, ["config", "set", "--global", "FOO=global", "BOTH=global_g"])
        assert result.exit_code == 0
        from platformdirs import PlatformDirs
        cfg_file = Path(PlatformDirs("doc_ai").user_config_dir) / "config.json"
        data = json.loads(cfg_file.read_text())
        assert data["FOO"] == "global"

        result = runner.invoke(cli.app, ["config", "set", "FOO=local", "BOTH=local_l"])
        assert result.exit_code == 0
        assert "FOO=local" in Path(".env").read_text()

        monkeypatch.setenv("FOO", "env")
        result = runner.invoke(cli.app, ["config", "show"])
        assert result.exit_code == 0
        foo = _parse_line(result.stdout, "FOO")
        assert foo[1] == "env"
        assert foo[2] == "local"
        assert foo[3] == "global"
        both = _parse_line(result.stdout, "BOTH")
        assert both[1] == "local_l"
        assert both[2] == "local_l"
        assert both[3] == "global_g"
