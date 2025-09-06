import io
import logging

import click
import questionary
import typer

from doc_ai.cli import utils


class RaisingQuestion:
    def ask(self):
        raise questionary.ValidationError("boom")


def make_ctx():
    ctx = typer.Context(click.Command("x"))
    ctx.obj = {"interactive": True}
    return ctx


def test_prompt_if_missing_questionary_error(monkeypatch, caplog):
    ctx = make_ctx()
    monkeypatch.setattr(
        utils.sys, "stdin", type("Tty", (io.StringIO,), {"isatty": lambda self: True})()
    )
    monkeypatch.setattr(utils.questionary, "text", lambda *a, **k: RaisingQuestion())
    with caplog.at_level(logging.WARNING):
        result = utils.prompt_if_missing(ctx, None, "Prompt")
    assert result is None
    assert any("Prompt failed" in r.message for r in caplog.records)


def test_select_doc_type_questionary_error(monkeypatch):
    ctx = make_ctx()
    monkeypatch.setattr(utils, "discover_doc_types_topics", lambda: (["reports"], None))
    monkeypatch.setattr(utils.questionary, "select", lambda *a, **k: RaisingQuestion())
    monkeypatch.setattr(utils, "prompt_if_missing", lambda c, v, m: "reports")
    result = utils.select_doc_type(ctx, None)
    assert result == "reports"


def test_select_topic_questionary_error(monkeypatch):
    ctx = make_ctx()
    monkeypatch.setattr(utils, "discover_topics", lambda d: ["topic1"])
    monkeypatch.setattr(utils.questionary, "select", lambda *a, **k: RaisingQuestion())
    monkeypatch.setattr(utils, "prompt_if_missing", lambda c, v, m: "topic1")
    result = utils.select_topic(ctx, "reports", None)
    assert result == "topic1"
