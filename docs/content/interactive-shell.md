---
title: Interactive Shell
---

The `doc_ai.cli.interactive` module exposes a small set of **typed, reusable APIs**
for adding an interactive prompt to any [Typer](https://typer.tiangolo.com/) application.

## Running a shell

```python
from doc_ai import cli

# Launch the project's own CLI in interactive mode
cli.interactive_shell(cli.app)
```

The shell provides readline based tab-completion, remembers command history
across sessions, and is safe to reuse in other Typer based projects.

## Programmatic completions

Completions can also be queried directly for custom tooling:

```python
from doc_ai.cli import app
from doc_ai.cli import get_completions

get_completions(app, "co", "co")
# ['convert']
```

The package ships a `py.typed` marker so these functions are fully typed when
used with static type checkers such as `mypy` or `pyright`.
