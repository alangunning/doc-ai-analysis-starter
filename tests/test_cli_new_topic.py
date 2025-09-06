import shutil
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from doc_ai.cli import app


def test_new_topic_management():
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

        topic_result = runner.invoke(
            app,
            [
                "new",
                "topic",
                "biology",
                "--doc-type",
                "sample",
                "--description",
                "desc",
            ],
        )
        assert topic_result.exit_code == 0
        target_file = Path("data/sample/sample.analysis.biology.prompt.yaml")
        assert target_file.is_file()
        desc_file = Path(
            "data/sample/sample.analysis.biology.prompt.description.txt"
        )
        assert desc_file.read_text().strip() == "desc"

        with patch("doc_ai.cli.new_topic.sys.stdin.isatty", return_value=True):
            rename_res = runner.invoke(
                app,
                [
                    "new",
                    "rename-topic",
                    "biology",
                    "chemistry",
                    "--doc-type",
                    "sample",
                ],
                input="y\n",
            )
        assert rename_res.exit_code == 0
        assert not target_file.exists()
        renamed = Path("data/sample/sample.analysis.chemistry.prompt.yaml")
        assert renamed.is_file()
        assert Path(
            "data/sample/sample.analysis.chemistry.prompt.description.txt"
        ).is_file()

        with patch("doc_ai.cli.new_topic.sys.stdin.isatty", return_value=True):
            del_res = runner.invoke(
                app, ["new", "delete-topic", "chemistry", "--doc-type", "sample"], input="y\n"
            )
        assert del_res.exit_code == 0
        assert not renamed.exists()
        assert not Path(
            "data/sample/sample.analysis.chemistry.prompt.description.txt"
        ).exists()

