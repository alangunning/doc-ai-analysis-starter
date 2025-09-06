import shutil
from pathlib import Path

import click
from typer.main import get_command

import doc_ai.cli.interactive as interactive
from doc_ai import plugins
from doc_ai.cli import app


def _setup_ctx() -> click.Context:
    plugins._reset()
    cmd = get_command(app)
    ctx = click.Context(cmd)
    interactive._register_repl_commands(ctx)
    comp = interactive.DocAICompleter(cmd, ctx)
    interactive.PROMPT_KWARGS = {"completer": comp}
    return ctx, comp


class DummyForm:
    def __init__(self, answers):
        self._answers = answers

    def ask(self):
        return self._answers


def test_wizard_flows_update_files_and_completions(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    repo_root = Path(__file__).resolve().parents[1]
    prompts_dir = Path(".github/prompts")
    prompts_dir.mkdir(parents=True)
    shutil.copy(
        repo_root / ".github/prompts/doc-analysis.analysis.prompt.yaml",
        prompts_dir / "doc-analysis.analysis.prompt.yaml",
    )
    shutil.copy(
        repo_root / ".github/prompts/validate-output.validate.prompt.yaml",
        prompts_dir / "validate-output.validate.prompt.yaml",
    )
    shutil.copy(
        repo_root / ".github/prompts/doc-analysis.topic.prompt.yaml",
        prompts_dir / "doc-analysis.topic.prompt.yaml",
    )

    _setup_ctx()

    # Replace interactive questionary builders with no-op stubs
    monkeypatch.setattr(interactive.questionary, "text", lambda *a, **k: None)
    monkeypatch.setattr(interactive.questionary, "select", lambda *a, **k: None)

    # New document type wizard
    monkeypatch.setattr(
        interactive.questionary,
        "form",
        lambda **qs: DummyForm({"name": "sample", "description": "desc"}),
    )
    interactive._repl_wizard(["new-doc-type"])
    assert Path("data/sample/sample.analysis.prompt.yaml").is_file()
    comp = interactive.PROMPT_KWARGS["completer"]
    assert "sample" in comp._doc_types.words

    # New topic wizard
    monkeypatch.setattr(
        interactive.questionary,
        "form",
        lambda **qs: DummyForm(
            {"doc_type": "sample", "topic": "biology", "description": "desc"}
        ),
    )
    interactive._repl_wizard(["new-topic"])
    assert Path("data/sample/sample.analysis.biology.prompt.yaml").is_file()
    comp = interactive.PROMPT_KWARGS["completer"]
    assert "biology" in comp._topics.words

    # Bulk URL wizard
    monkeypatch.setattr(
        interactive.questionary,
        "form",
        lambda **qs: DummyForm(
            {
                "doc_type": "sample",
                "urls": "https://example.com\nhttps://example.org",
            }
        ),
    )
    interactive._repl_wizard(["urls"])
    urls_path = Path("data/sample/urls.txt")
    assert urls_path.read_text().splitlines() == [
        "https://example.com",
        "https://example.org",
    ]
