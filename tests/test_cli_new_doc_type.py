import shutil
from pathlib import Path

from typer.testing import CliRunner

from doc_ai.cli import app


def test_new_doc_type_creates_scaffolding():
    runner = CliRunner()
    repo_root = Path(__file__).resolve().parents[1]
    analysis_tpl = repo_root / ".github" / "prompts" / "doc-analysis.analysis.prompt.yaml"
    validate_tpl = repo_root / ".github" / "prompts" / "validate-output.validate.prompt.yaml"

    with runner.isolated_filesystem():
        prompts_dir = Path(".github/prompts")
        prompts_dir.mkdir(parents=True)
        shutil.copy(analysis_tpl, prompts_dir / "doc-analysis.analysis.prompt.yaml")
        shutil.copy(validate_tpl, prompts_dir / "validate-output.validate.prompt.yaml")

        result = runner.invoke(app, ["new", "doc-type", "sample"])
        assert result.exit_code == 0

        new_dir = Path("data/sample")
        assert new_dir.is_dir()
        assert (new_dir / "sample.analysis.prompt.yaml").is_file()
        assert (new_dir / "validate.prompt.yaml").is_file()
