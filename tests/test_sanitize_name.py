import shutil
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from doc_ai.cli import app
from doc_ai.cli.utils import sanitize_name


def _setup_templates() -> tuple[Path, Path]:
    repo_root = Path(__file__).resolve().parents[1]
    analysis_tpl = repo_root / ".github" / "prompts" / "doc-analysis.analysis.prompt.yaml"
    validate_tpl = repo_root / ".github" / "prompts" / "validate-output.validate.prompt.yaml"
    return analysis_tpl, validate_tpl


def test_sanitize_name_valid():
    assert sanitize_name("Valid_Name-123") == "Valid_Name-123"


def test_sanitize_name_invalid():
    with pytest.raises(typer.BadParameter):
        sanitize_name("bad name!")


def test_sanitize_name_path_traversal():
    with pytest.raises(typer.BadParameter):
        sanitize_name("../secret")


def test_cli_rejects_path_traversal():
    runner = CliRunner()
    analysis_tpl, validate_tpl = _setup_templates()

    with runner.isolated_filesystem():
        prompts_dir = Path(".github/prompts")
        prompts_dir.mkdir(parents=True)
        shutil.copy(analysis_tpl, prompts_dir / "doc-analysis.analysis.prompt.yaml")
        shutil.copy(validate_tpl, prompts_dir / "validate-output.validate.prompt.yaml")

        result = runner.invoke(app, ["new", "doc-type", "../secret"])
        assert result.exit_code != 0
        assert "Invalid name" in result.output
