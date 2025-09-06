import runpy

import click
from prompt_toolkit.document import Document
from typer.main import get_command

from doc_ai import plugins
from doc_ai.batch import _parse_command
from doc_ai.cli.interactive import DocAICompleter


def test_example_plugin_repl_and_completion(capsys):
    plugins._reset()
    module = runpy.run_path("docs/content/examples/plugin_example.py")

    assert "ping" in plugins.iter_repl_commands()
    _parse_command("ping")
    assert "pong" in capsys.readouterr().out

    typer_app = module["app"]
    click_cmd = get_command(typer_app)
    ctx = click.Context(click_cmd)
    comp = DocAICompleter(click_cmd, ctx)
    completions = {c.text for c in comp.get_completions(Document("hello "), None)}
    assert {"apple", "banana", "cherry"} <= completions
    plugins._reset()
