import io
from pathlib import Path
import click
import typer

from doc_ai.cli import convert as convert_mod
from doc_ai.cli import embed as embed_mod
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


def test_convert_missing_source_no_interactive_flag(monkeypatch):
    monkeypatch.setattr(
        utils.sys, "stdin", type("Tty", (io.StringIO,), {"isatty": lambda self: True})()
    )

    def fail_prompt(*args, **kwargs):
        raise AssertionError("prompt should not be called")

    monkeypatch.setattr(utils.questionary, "text", fail_prompt)

    def fail_convert_path(*args, **kwargs):
        raise AssertionError("convert should not run")

    monkeypatch.setattr("doc_ai.cli.convert_path", fail_convert_path)

    ctx = typer.Context(click.Command("convert"))
    ctx.obj = {"config": {}, "interactive": False}
    try:
        convert_mod.convert(ctx, None, [], None, None, [], False)
    except typer.BadParameter:
        pass
    else:
        raise AssertionError("BadParameter not raised")


def test_embed_prompts_for_missing_source(monkeypatch, tmp_path):
    monkeypatch.setattr(
        utils.questionary, "text", lambda *a, **k: DummyQuestion(str(tmp_path))
    )
    monkeypatch.setattr(
        utils.sys, "stdin", type("Tty", (io.StringIO,), {"isatty": lambda self: True})()
    )

    captured = {}

    def fake_build_vector_store(src, *, fail_fast=False, workers=1):
        captured["src"] = src

    monkeypatch.setattr(embed_mod, "build_vector_store", fake_build_vector_store)

    ctx = typer.Context(click.Command("embed"))
    ctx.obj = {"config": {}}
    embed_mod.embed(ctx, None, False, 1)
    assert captured["src"] == tmp_path


def test_embed_missing_source_no_interactive(monkeypatch):
    monkeypatch.setattr(
        utils.sys, "stdin", type("Tty", (io.StringIO,), {"isatty": lambda self: True})()
    )

    def fail_prompt(*args, **kwargs):
        raise AssertionError("prompt should not be called")

    monkeypatch.setattr(utils.questionary, "text", fail_prompt)

    def fail_build(*args, **kwargs):
        raise AssertionError("embed should not run")

    monkeypatch.setattr(embed_mod, "build_vector_store", fail_build)

    ctx = typer.Context(click.Command("embed"))
    ctx.obj = {"config": {}, "interactive": False}
    try:
        embed_mod.embed(ctx, None, False, 1)
    except typer.BadParameter:
        pass
    else:
        raise AssertionError("BadParameter not raised")


def test_select_doc_type(monkeypatch):
    ctx = typer.Context(click.Command("dummy"))
    ctx.obj = {"config": {}}
    monkeypatch.setattr(
        utils, "discover_doc_types_topics", lambda: (["letters"], [])
    )
    monkeypatch.setattr(
        utils.questionary, "select", lambda *a, **k: DummyQuestion("letters")
    )
    assert utils.select_doc_type(ctx, None) == "letters"


def test_select_topic(monkeypatch):
    ctx = typer.Context(click.Command("dummy"))
    ctx.obj = {"config": {}}
    monkeypatch.setattr(utils, "discover_topics", lambda doc_type: ["old"])
    monkeypatch.setattr(
        utils.questionary, "select", lambda *a, **k: DummyQuestion("old")
    )
    assert utils.select_topic(ctx, None, "letters") == "old"
