import importlib
import os
import stat
from pathlib import Path

import pytest
from typer.testing import CliRunner


def test_global_config_permissions(monkeypatch):
    if os.name == "nt":
        pytest.skip("POSIX permissions not supported on Windows")
    runner = CliRunner()
    with runner.isolated_filesystem():
        cfg_dir = Path("confdir")
        cfg_path = cfg_dir / "config.json"
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", cfg_dir)
        monkeypatch.setattr(cli, "GLOBAL_CONFIG_PATH", cfg_path)
        cli.save_global_config({"a": "1"})
        dir_mode = stat.S_IMODE(cfg_dir.stat().st_mode)
        file_mode = stat.S_IMODE(cfg_path.stat().st_mode)
        assert dir_mode == 0o700
        assert file_mode == 0o600
