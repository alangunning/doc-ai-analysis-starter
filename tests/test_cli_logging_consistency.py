import re
from pathlib import Path

from typer.testing import CliRunner

import doc_ai.cli as cli

runner = CliRunner()


def test_root_logging_options_propagate(tmp_path):
    log_path = tmp_path / "cli.log"
    result = runner.invoke(
        cli.app,
        ["--log-level", "INFO", "--log-file", str(log_path), "config", "show"],
    )
    assert result.exit_code == 0
    assert re.search(r"log_level: INFO", result.stdout)
    assert re.search(rf"log_file: {re.escape(str(log_path))}", result.stdout)


def test_subcommand_logging_options_error():
    result = runner.invoke(cli.app, ["config", "show", "--log-level", "DEBUG"])
    assert result.exit_code != 0
    assert "No such option" in result.stderr or "No such option" in result.stdout
