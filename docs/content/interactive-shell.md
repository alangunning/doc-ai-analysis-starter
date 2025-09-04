---
title: Interactive Shell
---

The `doc_ai.cli.interactive` module exposes a **typed, reusable API** for adding
an interactive prompt to any [Typer](https://typer.tiangolo.com/) application.

## Running a shell

Start the REPL by running the `doc-ai` console script with no arguments:

```bash
doc-ai
doc-ai-analysis-starter> help
```

The prompt updates to reflect the current working directory and command
history is stored in ``~/.doc-ai-history`` for future sessions. Under the hood
the shell leverages ``click-repl`` to provide tab completion and can be reused
in other Typer-based projects.

## Built-in commands

The interactive prompt includes a minimal set of shell-like commands.
Use ``cd <path>`` to change the current working directory for subsequent
commands:

```
doc-ai-analysis-starter> cd docs
docs>
```

The package ships a ``py.typed`` marker so these functions are fully typed when
used with static type checkers such as ``mypy`` or ``pyright``.

## Programmatic usage

The same helper can power shells in other Typer applications:

```python
from doc_ai.cli import app, interactive_shell

interactive_shell(app)
```
