---
title: Plugin System
sidebar_position: 7
---

# Plugin System

Doc AI can be extended by third‑party packages that expose extra Typer
commands. Plugins must return a `typer.Typer` instance and register it under
the `doc_ai.plugins` entry‑point group so the main CLI can discover and
attach it at runtime. Plugins may also hook into the interactive REPL by
registering custom commands or completion providers via
`doc_ai.plugins`.

## Plugin template

The minimal plugin below adds a `hello` command. Use it as a starting point:

```python title="docs/examples/plugin_example.py"
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
```

Declare the Typer app in your package's `pyproject.toml` so doc‑ai can load
it:

```toml title="pyproject.toml"
[project.entry-points."doc_ai.plugins"]
"example" = "plugin_example:app"
```

Install the package in the same environment as `doc-ai` and the command will
appear automatically. For debugging, list the active plugins:

```bash
$ doc-ai plugins list
example
```

Trusted plugin names are stored in the global configuration file. Add a
plugin to the allowlist with `doc-ai plugins trust NAME` and remove it with
`doc-ai plugins untrust NAME`. Untrusting a plugin removes it from the
allowlist and unloads it from the current CLI session.

See the [template plugin](../../../examples/plugin_example.py) for a complete
file and entry‑point declaration.

