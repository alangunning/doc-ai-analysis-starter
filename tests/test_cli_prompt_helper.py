import io
from pathlib import Path
import click
import typer

from doc_ai.cli import convert as convert_mod
import doc_ai.cli.utils as utils


class DummyQuestion:
    def __init__(self, answer: str) -> None:
        self.answer = answer

    def ask(self) -> str:
        return self.answer


def test_convert_prompts_for_missing_source(monkeypatch, tmp_path):
    test_file = tmp_path / "sample.pdf"
    test_file.write_text("data", encoding="utf-8")

    monkeypatch.setattr(utils.questionary, "text", lambda *a, **k: DummyQuestion(str(test_file)))
    monkeypatch.setattr(utils.sys, "stdin", type("Tty", (io.StringIO,), {"isatty": lambda self: True})())

    called = {}

    def fake_convert_path(src, fmts, force=False):
        called["source"] = Path(src)
        return {}

    monkeypatch.setattr("doc_ai.cli.convert_path", fake_convert_path)

    ctx = typer.Context(click.Command("convert"))
    ctx.obj = {"config": {}}
    convert_mod.convert(ctx, None, [], None, None, [], False)
    assert called["source"] == test_file


def test_convert_missing_source_non_interactive(monkeypatch):
    monkeypatch.setattr(utils.sys, "stdin", io.StringIO())

    def fail_prompt(*args, **kwargs):
        raise AssertionError("prompt should not be called")

    monkeypatch.setattr(utils.questionary, "text", fail_prompt)

    def fail_convert_path(*args, **kwargs):
        raise AssertionError("convert should not run")

    monkeypatch.setattr("doc_ai.cli.convert_path", fail_convert_path)

    ctx = typer.Context(click.Command("convert"))
    ctx.obj = {"config": {}}
    try:
        convert_mod.convert(ctx, None, [], None, None, [], False)
    except typer.BadParameter:
        pass
    else:
        raise AssertionError("BadParameter not raised")
