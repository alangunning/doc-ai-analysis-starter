import importlib
from pathlib import Path

from typer.testing import CliRunner


def test_pipeline_dry_run_does_not_create_outputs():
    runner = CliRunner()
    with runner.isolated_filesystem():
        docs = Path("docs")
        docs.mkdir()
        (docs / "sample.pdf").write_text("raw")
        cli = importlib.import_module("doc_ai.cli")
        result = runner.invoke(cli.app, ["pipeline", "--dry-run", "docs"])
        assert result.exit_code == 0
        assert not list(docs.rglob("*.converted*"))
        assert not list(docs.rglob("*.analysis*"))

