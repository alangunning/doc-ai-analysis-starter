import shutil
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from doc_ai.cli import app


def _setup_templates() -> tuple[Path, Path]:
    repo_root = Path(__file__).resolve().parents[1]
    analysis_tpl = (
        repo_root / ".github" / "prompts" / "doc-analysis.analysis.prompt.yaml"
    )
    validate_tpl = (
        repo_root / ".github" / "prompts" / "validate-output.validate.prompt.yaml"
    )
    return analysis_tpl, validate_tpl


def test_new_doc_type_creates_scaffolding():
    runner = CliRunner()
    analysis_tpl, validate_tpl = _setup_templates()

    with runner.isolated_filesystem():
        prompts_dir = Path(".github/prompts")
        prompts_dir.mkdir(parents=True)
        shutil.copy(analysis_tpl, prompts_dir / "doc-analysis.analysis.prompt.yaml")
        shutil.copy(validate_tpl, prompts_dir / "validate-output.validate.prompt.yaml")

        result = runner.invoke(
            app,
            ["new", "doc-type", "sample", "--description", "description"],
        )
        assert result.exit_code == 0

        new_dir = Path("data/sample")
        assert new_dir.is_dir()
        assert (new_dir / "sample.analysis.prompt.yaml").is_file()
        assert (new_dir / "validate.prompt.yaml").is_file()
        assert (new_dir / "description.txt").read_text().strip() == "description"


def test_new_doc_type_prompts_for_name():
    runner = CliRunner()
    analysis_tpl, validate_tpl = _setup_templates()

    with runner.isolated_filesystem():
        prompts_dir = Path(".github/prompts")
        prompts_dir.mkdir(parents=True)
        shutil.copy(analysis_tpl, prompts_dir / "doc-analysis.analysis.prompt.yaml")
        shutil.copy(validate_tpl, prompts_dir / "validate-output.validate.prompt.yaml")

        with patch("doc_ai.cli.new_doc_type.prompt_if_missing", return_value="sample"):
            result = runner.invoke(
                app,
                ["new", "doc-type", "--description", "description"],
            )
        assert result.exit_code == 0

        new_dir = Path("data/sample")
        assert new_dir.is_dir()
        assert (new_dir / "sample.analysis.prompt.yaml").is_file()
        assert (new_dir / "validate.prompt.yaml").is_file()
        assert (new_dir / "description.txt").read_text().strip() == "description"


def test_rename_and_delete_doc_type_yes_and_non_interactive():
    runner = CliRunner()
    analysis_tpl, validate_tpl = _setup_templates()

    with runner.isolated_filesystem():
        prompts_dir = Path(".github/prompts")
        prompts_dir.mkdir(parents=True)
        shutil.copy(analysis_tpl, prompts_dir / "doc-analysis.analysis.prompt.yaml")
        shutil.copy(validate_tpl, prompts_dir / "validate-output.validate.prompt.yaml")

        runner.invoke(app, ["new", "doc-type", "old"])
        # add a topic to ensure rename updates topic files
        topic_tpl = Path(".github/prompts/doc-analysis.topic.prompt.yaml")
        repo_root = Path(__file__).resolve().parents[1]
        shutil.copy(
            repo_root / ".github" / "prompts" / "doc-analysis.topic.prompt.yaml",
            topic_tpl,
        )
        runner.invoke(app, ["new", "topic", "biology", "--doc-type", "old"])

        with patch("doc_ai.cli.new_doc_type.sys.stdin.isatty", return_value=True):
            rename_res = runner.invoke(
                app,
                [
                    "new",
                    "rename-doc-type",
                    "new",
                    "--doc-type",
                    "old",
                    "--yes",
                ],
            )
        assert rename_res.exit_code == 0
        assert Path("data/new/new.analysis.prompt.yaml").is_file()
        assert Path("data/new/new.analysis.biology.prompt.yaml").is_file()

        with patch("doc_ai.cli.new_doc_type.sys.stdin.isatty", return_value=True):
            del_res = runner.invoke(
                app, ["new", "delete-doc-type", "--doc-type", "new", "--yes"]
            )
        assert del_res.exit_code == 0
        assert not Path("data/new").exists()

        # non-interactive rename and delete
        runner.invoke(app, ["new", "doc-type", "temp"])
        with patch("doc_ai.cli.new_doc_type.sys.stdin.isatty", return_value=False):
            rename_res2 = runner.invoke(
                app, ["new", "rename-doc-type", "temp2", "--doc-type", "temp"]
            )
        assert rename_res2.exit_code == 0
        assert Path("data/temp2/temp2.analysis.prompt.yaml").is_file()

        with patch("doc_ai.cli.new_doc_type.sys.stdin.isatty", return_value=False):
            del_res2 = runner.invoke(
                app, ["new", "delete-doc-type", "--doc-type", "temp2"]
            )
        assert del_res2.exit_code == 0
        assert not Path("data/temp2").exists()


def test_duplicate_doc_type(tmp_path):
    runner = CliRunner()
    analysis_tpl, validate_tpl = _setup_templates()
    repo_root = Path(__file__).resolve().parents[1]
    topic_tpl = repo_root / ".github" / "prompts" / "doc-analysis.topic.prompt.yaml"

    with runner.isolated_filesystem():
        prompts_dir = Path(".github/prompts")
        prompts_dir.mkdir(parents=True)
        shutil.copy(analysis_tpl, prompts_dir / "doc-analysis.analysis.prompt.yaml")
        shutil.copy(validate_tpl, prompts_dir / "validate-output.validate.prompt.yaml")
        shutil.copy(topic_tpl, prompts_dir / "doc-analysis.topic.prompt.yaml")

        runner.invoke(app, ["new", "doc-type", "source"])
        runner.invoke(app, ["new", "topic", "biology", "--doc-type", "source"])

        with patch("doc_ai.cli.new_doc_type.sys.stdin.isatty", return_value=True):
            dup_res = runner.invoke(
                app,
                [
                    "new",
                    "duplicate-doc-type",
                    "copy",
                    "--doc-type",
                    "source",
                    "--yes",
                ],
            )
        assert dup_res.exit_code == 0
        # original remains
        assert Path("data/source/source.analysis.prompt.yaml").is_file()
        assert Path("data/source/source.analysis.biology.prompt.yaml").is_file()
        # duplicate has renamed files
        assert Path("data/copy/copy.analysis.prompt.yaml").is_file()
        assert Path("data/copy/copy.analysis.biology.prompt.yaml").is_file()
        assert Path("data/copy/validate.prompt.yaml").is_file()


def test_edit_doc_type_opens_prompt():
    runner = CliRunner()
    analysis_tpl, validate_tpl = _setup_templates()

    with runner.isolated_filesystem():
        prompts_dir = Path(".github/prompts")
        prompts_dir.mkdir(parents=True)
        shutil.copy(analysis_tpl, prompts_dir / "doc-analysis.analysis.prompt.yaml")
        shutil.copy(validate_tpl, prompts_dir / "validate-output.validate.prompt.yaml")

        runner.invoke(app, ["new", "doc-type", "sample"])

        target_file = Path("data/sample/sample.analysis.prompt.yaml")
        with patch("doc_ai.cli.new_doc_type.click.edit") as edit_mock:
            edit_mock.return_value = ""
            res = runner.invoke(app, ["new", "edit-doc-type", "--doc-type", "sample"])
        assert res.exit_code == 0
        edit_mock.assert_called_once_with(filename=str(target_file))
