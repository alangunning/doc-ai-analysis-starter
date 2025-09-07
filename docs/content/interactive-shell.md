---
title: Interactive Shell
---

The `doc_ai.cli.interactive` module exposes a **typed, reusable API** for adding
an interactive prompt to any [Typer](https://typer.tiangolo.com/) application.

## Running a shell

Start the REPL by running the `doc-ai` console script with no arguments:

```bash
doc-ai
doc-ai> help
```

The prompt updates to reflect the current working directory and command
history is stored in the user data directory provided by
``platformdirs`` (for example ``~/.local/share/doc_ai/history`` on Linux)
for future sessions. Set ``DOC_AI_HISTORY_FILE`` to override the history
location or ``-`` to disable it. The ``:clear-history`` REPL command
truncates the file during a session. Under the hood the shell leverages
``click-repl`` to provide tab completion and can be reused in other
Typer-based projects.

Use `show doc-types` and `show topics` to list document types under the
``data/`` directory and analysis topics discovered from prompt files.

## Safe environment variables

Only a minimal set of environment variables is available for completion inside
the REPL and forwarded to shell escapes. When the
:envvar:`DOC_AI_SAFE_ENV_VARS` setting is unset, only ``PATH`` and ``HOME`` are
suggested and passed to child processes. To expose additional variables, either
set ``DOC_AI_SAFE_ENV_VARS`` to a comma-separated allow/deny list or run
``doc-ai config safe-env`` subcommands. Items prefixed with ``-`` are denied and
the ``+`` prefix is optional.

Examples::

    DOC_AI_SAFE_ENV_VARS=MY_API_KEY,-DEBUG_TOKEN
    doc-ai config safe-env add MY_API_KEY

Variables not present in the allow list are omitted from completion results and
stripped from the environment of shell escapes, reducing the risk of accidental
secret disclosure.

## Built-in commands

The interactive prompt includes a minimal set of shell-like commands.
Use ``cd <path>`` to change the current working directory for subsequent
commands. The command reloads any ``.env`` file and global configuration
in the target directory so project-specific settings take effect. Other
helpers include ``:delete-doc-type`` and ``:delete-topic`` for removing
prompt files and ``:set-default DOC_TYPE [TOPIC]`` to persist defaults.
Shell escapes (``!command``) are disabled by default. Set
``DOC_AI_ALLOW_SHELL=true`` to enable them—doing so emits a warning when the
REPL starts. Enabled commands only receive allowlisted environment variables;
others are removed. When disabled, using ``!`` emits a warning.

```
doc-ai> cd docs
docs>
```

Switching directories lets you pick up new settings without restarting:

```
doc-ai> config show OPENAI_MODEL
gpt-4o-mini
doc-ai> cd ../another-project
another-project> config show OPENAI_MODEL
gpt-4o
```

See the [cd command](https://github.com/alangunning/doc-ai#cd-command) in the project README for more details.

The package ships a ``py.typed`` marker so these functions are fully typed when
used with static type checkers such as ``mypy`` or ``pyright``.

## Programmatic usage

The same helper can power shells in other Typer applications:

```python
from doc_ai.cli import app, interactive_shell

interactive_shell(app)
```
