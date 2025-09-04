---
title: Interactive Shell
---

Doc AI Starter exposes an interactive shell powered by
[click-repl](https://github.com/click-contrib/click-repl). Launch it by running
the `doc-ai` command without arguments:

```bash
$ doc-ai
doc-ai> help
...
doc-ai> exit
```

The shell provides readline tab-completion, remembers command history across
sessions, and respects the global `--log-level` and `--log-file` options:

```bash
$ doc-ai --log-level debug --log-file run.log
doc-ai>
```

For custom tooling, completions can be queried directly:

```python
from doc_ai.cli import app, get_completions

get_completions(app, "co", "co")
# ['convert']
```

The package ships a `py.typed` marker so these functions are fully typed when
used with static type checkers such as `mypy` or `pyright`.
