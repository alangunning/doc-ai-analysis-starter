---
title: Plugin System
sidebar_position: 7
---

# Plugin System

Doc AI can be extended by third‑party packages that expose extra Typer
commands. Plugins must return a `typer.Typer` instance and register it under
the `doc_ai.plugins` entry‑point group so the main CLI can discover and
attach it at runtime.

## Plugin template

The minimal plugin below adds a `hello` command. Use it as a starting point:

```python title="docs/examples/plugin_example.py"
import typer

app = typer.Typer(help="Example doc-ai plugin")

@app.command()
def hello(name: str = "World") -> None:
    """Greet someone from the plugin."""
    typer.echo(f"Hello {name}!")
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

See the [template plugin](../../../examples/plugin_example.py) for a complete
file and entry‑point declaration.

