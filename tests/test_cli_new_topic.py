import shutil
from pathlib import Path

from typer.testing import CliRunner

from doc_ai.cli import app


def test_new_topic_creates_prompt_file():
    runner = CliRunner()
    repo_root = Path(__file__).resolve().parents[1]
    analysis_tpl = repo_root / ".github" / "prompts" / "doc-analysis.analysis.prompt.yaml"
    validate_tpl = repo_root / ".github" / "prompts" / "validate-output.validate.prompt.yaml"
    topic_tpl = repo_root / ".github" / "prompts" / "doc-analysis.topic.prompt.yaml"

    with runner.isolated_filesystem():
        prompts_dir = Path(".github/prompts")
        prompts_dir.mkdir(parents=True)
        shutil.copy(analysis_tpl, prompts_dir / "doc-analysis.analysis.prompt.yaml")
        shutil.copy(validate_tpl, prompts_dir / "validate-output.validate.prompt.yaml")
        shutil.copy(topic_tpl, prompts_dir / "doc-analysis.topic.prompt.yaml")

        result = runner.invoke(app, ["new", "doc-type", "sample"])
        assert result.exit_code == 0

        topic_result = runner.invoke(app, ["new", "topic", "sample", "biology"])
        assert topic_result.exit_code == 0

        target_file = Path("data/sample/sample.analysis.biology.prompt.yaml")
        assert target_file.is_file()
