import io

import click
import pytest
import typer

pytest.importorskip("questionary")

from doc_ai.cli import config as config_mod


class DummyQuestion:
    def __init__(self, answer: str) -> None:
        self.answer = answer

    def ask(self) -> str:
        return self.answer


def test_config_wizard_sets_values(monkeypatch):
    monkeypatch.setattr(config_mod, "load_env_defaults", lambda: {"FOO": "bar"})
    monkeypatch.setattr(
        config_mod.questionary, "text", lambda *a, **k: DummyQuestion("baz")
    )
    monkeypatch.setattr(
        config_mod.sys,
        "stdin",
        type("Tty", (io.StringIO,), {"isatty": lambda self: True})(),
    )

    captured = []

    def fake_set(ctx, pairs, use_global):
        captured.extend(pairs)

    monkeypatch.setattr(config_mod, "_set_pairs", fake_set)

    ctx = typer.Context(click.Command("wizard"))
    ctx.obj = {}
    config_mod.wizard(ctx, False)
    assert captured == ["FOO=baz"]


def test_config_wizard_non_interactive(monkeypatch):
    monkeypatch.setattr(config_mod, "load_env_defaults", lambda: {"FOO": "bar"})
    monkeypatch.setattr(config_mod.sys, "stdin", io.StringIO())

    def fail_prompt(*args, **kwargs):
        raise AssertionError("prompt should not be called")

    monkeypatch.setattr(config_mod.questionary, "text", fail_prompt)

    def fail_set(*args, **kwargs):
        raise AssertionError("should not write config")

    monkeypatch.setattr(config_mod, "_set_pairs", fail_set)

    ctx = typer.Context(click.Command("wizard"))
    ctx.obj = {}
    config_mod.wizard(ctx, False)
