from typing import Iterable

import typer
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

from doc_ai.plugins import register_completion_provider, register_repl_command

app = typer.Typer(help="Example doc-ai plugin")


@app.command()
def hello(name: str = "World") -> None:
    """Greet someone from the plugin."""
    typer.echo(f"Hello {name}!")


def _ping(args: list[str]) -> None:
    """Simple REPL command that prints a response."""

    typer.echo("pong")


register_repl_command("ping", _ping)


def _hello_completions(document: Document, _event) -> Iterable[Completion]:
    if document.text_before_cursor.startswith("hello "):
        for fruit in ["apple", "banana", "cherry"]:
            yield Completion(fruit, start_position=0)


register_completion_provider(_hello_completions)
