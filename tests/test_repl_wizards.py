import click
from typer.main import get_command

from doc_ai.cli import app
import doc_ai.cli.interactive as interactive
from doc_ai import plugins


class DummyForm:
    def __init__(self, answers):
        self._answers = answers

    def ask(self):
        return self._answers


def _setup_ctx(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    plugins._reset()
    ctx = click.Context(get_command(app))
    monkeypatch.setattr(interactive, "_REPL_CTX", ctx)
    interactive._register_repl_commands(ctx)
    return ctx


def test_wizard_new_doc_type_creates_files(monkeypatch, tmp_path):
    ctx = _setup_ctx(monkeypatch, tmp_path)

    tmpl_dir = tmp_path / ".github" / "prompts"
    tmpl_dir.mkdir(parents=True)
    (tmpl_dir / "doc-analysis.analysis.prompt.yaml").write_text("a")
    (tmpl_dir / "validate-output.validate.prompt.yaml").write_text("b")

    monkeypatch.setattr(interactive.questionary, "form", lambda **k: DummyForm({"name": "alpha", "description": ""}))
    monkeypatch.setattr(interactive.questionary, "text", lambda *a, **k: object())
    monkeypatch.setattr(interactive, "_textarea", lambda *a, **k: DummyForm({}))

    called = []
    monkeypatch.setattr(interactive, "refresh_completer", lambda: called.append(True))

    interactive._repl_wizard(["new-doc-type"])

    assert (tmp_path / "data" / "alpha" / "alpha.analysis.prompt.yaml").exists()
    assert called


def test_wizard_new_topic_creates_prompt(monkeypatch, tmp_path):
    ctx = _setup_ctx(monkeypatch, tmp_path)

    tmpl_dir = tmp_path / ".github" / "prompts"
    tmpl_dir.mkdir(parents=True)
    (tmpl_dir / "doc-analysis.topic.prompt.yaml").write_text("tmpl")
    (tmp_path / "data" / "alpha").mkdir(parents=True)

    monkeypatch.setattr(interactive, "discover_doc_types_topics", lambda: ([], {}))
    monkeypatch.setattr(
        interactive.questionary,
        "form",
        lambda **k: DummyForm({"doc_type": "alpha", "topic": "beta", "description": ""}),
    )
    monkeypatch.setattr(interactive.questionary, "text", lambda *a, **k: object())
    monkeypatch.setattr(interactive, "_textarea", lambda *a, **k: DummyForm({}))

    called = []
    monkeypatch.setattr(interactive, "refresh_completer", lambda: called.append(True))

    interactive._repl_wizard(["new-topic"])

    assert (tmp_path / "data" / "alpha" / "alpha.analysis.beta.prompt.yaml").exists()
    assert called


def test_edit_url_list_updates_file(monkeypatch, tmp_path):
    ctx = _setup_ctx(monkeypatch, tmp_path)

    (tmp_path / "data" / "alpha").mkdir(parents=True)
    monkeypatch.setattr(interactive, "discover_doc_types_topics", lambda: ([], {}))
    monkeypatch.setattr(
        interactive.questionary,
        "form",
        lambda **k: DummyForm({"doc_type": "alpha", "urls": "http://a.com\nhttps://b.com\n"}),
    )
    monkeypatch.setattr(interactive.questionary, "text", lambda *a, **k: object())
    monkeypatch.setattr(interactive, "_textarea", lambda *a, **k: DummyForm({}))

    called = []
    monkeypatch.setattr(interactive, "refresh_completer", lambda: called.append(True))

    interactive._repl_edit_url_list([])

    lines = (tmp_path / "data" / "alpha" / "urls.txt").read_text().splitlines()
    assert "http://a.com" in lines and "https://b.com" in lines
    assert called

