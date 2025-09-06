import io
import shutil
from pathlib import Path

import click
import typer
from typer.main import get_command
from typer.testing import CliRunner
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from doc_ai.cli import app
import doc_ai.cli.interactive as interactive
import doc_ai.cli.new_doc_type as new_doc_type_mod
import doc_ai.cli.new_topic as new_topic_mod
import doc_ai.cli.manage_urls as manage_urls_mod


class DummyForm:
    def __init__(self, answers):
        self.answers = answers

    def ask(self):
        return self.answers


class DummyTextarea:
    def __init__(self, text):
        self.text = text

    def ask(self):
        return self.text


def _setup_templates():
    repo_root = Path(__file__).resolve().parents[1]
    analysis = repo_root / ".github" / "prompts" / "doc-analysis.analysis.prompt.yaml"
    validate = repo_root / ".github" / "prompts" / "validate-output.validate.prompt.yaml"
    topic = repo_root / ".github" / "prompts" / "doc-analysis.topic.prompt.yaml"
    return analysis, validate, topic


def test_wizard_creates_resources_and_refreshes(monkeypatch):
    runner = CliRunner()
    analysis_tpl, validate_tpl, topic_tpl = _setup_templates()

    with runner.isolated_filesystem():
        prompts_dir = Path(".github/prompts")
        prompts_dir.mkdir(parents=True)
        shutil.copy(analysis_tpl, prompts_dir / "doc-analysis.analysis.prompt.yaml")
        shutil.copy(validate_tpl, prompts_dir / "validate-output.validate.prompt.yaml")
        shutil.copy(topic_tpl, prompts_dir / "doc-analysis.topic.prompt.yaml")

        monkeypatch.setattr(new_doc_type_mod.sys, "stdin", type("T", (io.StringIO,), {"isatty": lambda self: True})())
        monkeypatch.setattr(new_topic_mod.sys, "stdin", type("T", (io.StringIO,), {"isatty": lambda self: True})())
        monkeypatch.setattr(new_topic_mod.questionary, "form", lambda *a, **k: DummyForm({"doc_type": "sample", "topic": "biology", "description": ""}))
        monkeypatch.setattr(new_topic_mod.typer, "prompt", lambda *a, **k: "")

        calls = []
        monkeypatch.setattr(interactive, "refresh_completer", lambda: calls.append(True))

        ctx = typer.Context(click.Command("wizard"))
        ctx.obj = {"config": {}}

        # create document type directly
        new_doc_type_mod.doc_type(ctx, "sample", description="")
        assert Path("data/sample/sample.analysis.prompt.yaml").is_file()

        new_topic_mod.wizard(ctx)
        assert Path("data/sample/sample.analysis.biology.prompt.yaml").is_file()
        assert len(calls) >= 2

        completer = interactive.DocAICompleter(get_command(app), ctx)
        completer.refresh()
        words = [c.text for c in completer.get_completions(Document("pipeline "), CompleteEvent())]
        assert "sample" in words
        words = [c.text for c in completer.get_completions(Document("pipeline --topic "), CompleteEvent())]
        assert "biology" in words


def test_edit_url_list_saves(monkeypatch):
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("data/sample").mkdir(parents=True)

        monkeypatch.setattr(manage_urls_mod.questionary, "textarea", lambda *a, **k: DummyTextarea("https://a.com\nhttps://b.com\n"), raising=False)
        calls = []
        monkeypatch.setattr(manage_urls_mod, "refresh_completer", lambda: calls.append(True))

        ctx = typer.Context(click.Command("edit"))
        ctx.obj = {"config": {}}
        manage_urls_mod.edit_url_list(ctx, "sample")

        urls_path = Path("data/sample/urls.txt")
        assert urls_path.read_text().splitlines() == ["https://a.com", "https://b.com"]
        assert calls
