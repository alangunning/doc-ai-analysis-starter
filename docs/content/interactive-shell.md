---
title: Interactive Shell
---

The `doc_ai.cli.interactive` module exposes a **typed, reusable API** for adding
an interactive prompt to any [Typer](https://typer.tiangolo.com/) application.

## Running a shell

```python
from doc_ai import cli

# Launch the project's own CLI in interactive mode
cli.interactive_shell(cli.app)
```

The shell leverages ``click-repl`` to provide tab completion and persistent
history across sessions, and is safe to reuse in other Typer based projects.

The package ships a ``py.typed`` marker so these functions are fully typed when
used with static type checkers such as ``mypy`` or ``pyright``.
