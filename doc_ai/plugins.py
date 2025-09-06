"""Plugin registry for Doc AI.

Plugins can register additional REPL commands or completion providers by
calling the functions in this module at import time. Each registered callable
must conform to a specific signature so the host application knows how to
invoke it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Dict, List

from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

# Registered REPL commands: name -> callback accepting list of args.
_REPL_COMMANDS: Dict[str, Callable[[List[str]], None]] = {}

# Completion provider callables.
_COMPLETION_PROVIDERS: List[
    Callable[[Document, object | None], Iterable[Completion]]
] = []


def register_repl_command(name: str, func: Callable[[List[str]], None]) -> None:
    """Register *func* as a REPL command named *name*.

    The callback must have the signature ``(args: list[str]) -> None`` where
    *args* contains the remaining tokens from the input line.
    """

    _REPL_COMMANDS[name] = func


def iter_repl_commands() -> Dict[str, Callable[[List[str]], None]]:
    """Return the mapping of registered REPL commands."""

    return _REPL_COMMANDS


def register_completion_provider(
    provider: Callable[[Document, object | None], Iterable[Completion]]
) -> None:
    """Register a custom completion *provider*.

    The callable must match the signature ``(document: Document, event:
    object | None) -> Iterable[Completion]`` and should yield
    :class:`~prompt_toolkit.completion.Completion` objects.
    """

    _COMPLETION_PROVIDERS.append(provider)


def iter_completion_providers() -> (
    List[Callable[[Document, object | None], Iterable[Completion]]]
):
    """Return the registered completion providers."""

    return list(_COMPLETION_PROVIDERS)


def _reset() -> None:
    """Clear all registered plugins (for testing)."""

    _REPL_COMMANDS.clear()
    _COMPLETION_PROVIDERS.clear()


__all__ = [
    "register_repl_command",
    "register_completion_provider",
    "iter_repl_commands",
    "iter_completion_providers",
]
