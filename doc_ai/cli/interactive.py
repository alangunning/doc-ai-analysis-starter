"""Interactive REPL helper for the Doc AI CLI."""

from __future__ import annotations

import logging
import os
import re
import shlex
import stat
import subprocess
import warnings
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, TypeVar, cast

import click

# Replace deprecated MultiCommand with Group before importing click-repl
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", ".*'MultiCommand'.*", DeprecationWarning)
    click.MultiCommand = click.Group  # type: ignore[attr-defined]

import click_repl.utils as repl_utils
import questionary
import typer
from click.core import Command
from click.exceptions import Exit as ClickExit
from click_repl import ClickCompleter, repl
from click_repl import _repl as click_repl_repl
from platformdirs import PlatformDirs
from prompt_toolkit.completion import (
    CompleteEvent,
    Completer,
    Completion,
    WordCompleter,
)
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from typer.main import get_command

import doc_ai.batch as batch_mod
from doc_ai import plugins
from doc_ai.batch import run_batch

SAFE_ENV_VARS_ENV = "DOC_AI_SAFE_ENV_VARS"
"""Config key with comma-separated allow/deny env var names."""

ALLOW_SHELL_ENV = "DOC_AI_ALLOW_SHELL"
"""Configuration key that enables shell escapes when truthy."""

HISTORY_FILE_ENV = "DOC_AI_HISTORY_FILE"
"""Configuration key overriding or disabling REPL history."""

SAFE_ENV_VARS: set[str] = {"PATH", "HOME"}
"""Base names of environment variables that may be exposed in the REPL."""


def _parse_allow_deny(value: str | None = None) -> tuple[set[str], set[str]]:
    """Return allow and deny sets parsed from a comma-separated *value*.

    When *value* is ``None`` the minimal whitelist defined by ``SAFE_ENV_VARS``
    is returned.  Items prefixed with ``-`` are placed in the deny set; all
    others are considered allowed. Empty items are ignored. ``+`` prefixes are
    optional and treated the same as no prefix.
    """

    if value is None:
        return set(SAFE_ENV_VARS), set()

    allow: set[str] = set()
    deny: set[str] = set()
    for raw in value.split(","):
        name = raw.strip()
        if not name:
            continue
        if name.startswith("-"):
            deny.add(name[1:].strip())
        else:
            allow.add(name.lstrip("+").strip())
    return allow, deny


PROMPT_KWARGS: dict[str, object] | None = None
_REPL_CTX: click.Context | None = None
LAST_EXIT_CODE = 0

__all__ = [
    "interactive_shell",
    "run_batch",
    "DocAICompleter",
    "discover_doc_types_topics",
    "discover_topics",
    "SAFE_ENV_VARS",
    "PROMPT_KWARGS",
    "refresh_completer",
    "refresh_after",
    "_prompt_name",
    "LAST_EXIT_CODE",
]


logger = logging.getLogger(__name__)


def _allow_shell_from_config(cfg: Mapping[str, object]) -> bool:
    """Return ``True`` if shell escapes are explicitly allowed."""

    raw: object | None = cfg.get(ALLOW_SHELL_ENV)
    if raw is None:
        raw = os.getenv(ALLOW_SHELL_ENV, "")
    return str(raw).lower() in {"1", "true", "yes"}


def _allow_shell() -> bool:
    cfg: Mapping[str, object] = {}
    if _REPL_CTX and isinstance(_REPL_CTX.obj, dict):
        cfg = _REPL_CTX.obj.get("config", {})
    if not cfg:
        from . import read_configs  # local import to avoid circular

        try:
            _, _, merged = read_configs()
            cfg = merged
        except Exception:
            cfg = {}
    return _allow_shell_from_config(cfg)


def _dispatch_repl_commands(command: str) -> bool:
    """Execute system commands prefixed with ``!`` using ``subprocess.run``."""

    global LAST_EXIT_CODE
    if command.startswith("!"):
        if not _allow_shell():
            warnings.warn(
                f"Shell escapes disabled. Set {ALLOW_SHELL_ENV}=true to enable.",
                stacklevel=1,
            )
            LAST_EXIT_CODE = 1
            return True
        parts = shlex.split(command[1:])
        if not parts:
            LAST_EXIT_CODE = 0
            return True
        try:
            result = subprocess.run(parts, shell=False, capture_output=True, text=True)
        except FileNotFoundError:
            click.echo(f"{parts[0]}: command not found", err=True)
            LAST_EXIT_CODE = 127
            return True
        except PermissionError:
            click.echo(f"{parts[0]}: permission denied", err=True)
            LAST_EXIT_CODE = 126
            return True
        if result.stdout:
            click.echo(result.stdout, nl=False)
        if result.stderr:
            click.echo(result.stderr, err=True, nl=False)
        LAST_EXIT_CODE = result.returncode
        return True
    return False


# Patch click-repl helpers to use the custom dispatcher
repl_utils.dispatch_repl_commands = _dispatch_repl_commands
click_repl_repl.dispatch_repl_commands = _dispatch_repl_commands
setattr(batch_mod, "dispatch_repl_commands", _dispatch_repl_commands)


def _repl_help(args: list[str]) -> None:
    """Display help for CLI commands or the REPL itself."""

    if _REPL_CTX is None:
        click.echo("Help is unavailable.")
        return

    ctx = _REPL_CTX
    cmd: Any = ctx.command
    cur_ctx = ctx
    path: list[str] = []
    for arg in args:
        if isinstance(cmd, click.Group):  # type: ignore[arg-type]
            sub = cmd.get_command(cur_ctx, arg)
            if sub is None:
                click.echo(f"Unknown command: {' '.join(path + [arg])}")
                return
            path.append(arg)
            cur_ctx = click.Context(sub, info_name=arg, parent=cur_ctx)
            cmd = sub
        else:
            click.echo(f"{' '.join(path) or cmd.name} has no subcommand {arg}")
            return

    click.echo(cmd.get_help(cur_ctx))

    if not args:
        repl_cmds = sorted(
            name for name in plugins.iter_repl_commands() if name.startswith(":")
        )
        if repl_cmds:
            click.echo("\nREPL commands: " + ", ".join(repl_cmds))
            click.echo("Example: :history")
        click.echo("\nType ':help COMMAND' for command-specific help.")
    elif isinstance(cmd, click.Group):  # type: ignore[arg-type]
        subs = sorted(cmd.list_commands(cur_ctx))
        if subs:
            click.echo("\nSubcommands: " + ", ".join(subs))
            click.echo(f"Example: :help {' '.join(path + [subs[0]])}")
    else:
        example = " ".join(path or [cmd.name or ""]) + " --help"
        click.echo(f"\nExample: {example}")


def _repl_reload(args: list[str]) -> None:
    """Reload dynamic resources like completions."""

    refresh_completer()
    click.echo("Resources reloaded.")


def _repl_history(args: list[str]) -> None:
    """Display the current session history."""

    history = PROMPT_KWARGS.get("history") if PROMPT_KWARGS else None
    if not isinstance(history, FileHistory):
        click.echo("No history available.")
        return
    items = list(history.load_history_strings())
    for i, entry in enumerate(reversed(items), 1):
        click.echo(f"{i}: {entry}")


def _repl_config(args: list[str]) -> None:
    """Invoke the config command from the REPL."""
    if _REPL_CTX is None:
        click.echo("Config is unavailable.")
        return
    from doc_ai.cli import config as config_mod

    cmd = get_command(config_mod.app)
    sub_ctx: click.Context | None = None
    try:
        sub_ctx = cmd.make_context(
            "config", args, obj=_REPL_CTX.obj, default_map=_REPL_CTX.default_map
        )
        cmd.invoke(sub_ctx)
    except click.ClickException as exc:
        click.echo(exc.format_message())
    except ClickExit as exc:
        raise typer.Exit(exc.exit_code)
    finally:
        if sub_ctx is not None:
            _REPL_CTX.default_map = sub_ctx.default_map


def _repl_clear_history(args: list[str]) -> None:
    """Clear the REPL command history."""

    history = PROMPT_KWARGS.get("history") if PROMPT_KWARGS else None
    if not isinstance(history, FileHistory):
        click.echo("No history available.")
        return
    path = Path(str(history.filename))
    path.write_text("")
    assert PROMPT_KWARGS is not None
    PROMPT_KWARGS["history"] = FileHistory(path)
    click.echo("History cleared.")


def _repl_edit_prompt(args: list[str]) -> None:
    """Edit prompt for the current or given doc type/topic."""
    if _REPL_CTX is None:
        click.echo("Prompt editing unavailable.")
        return
    from .prompt import edit_prompt_inline

    cfg = _REPL_CTX.obj.get("config", {}) if _REPL_CTX.obj else {}
    doc_type = args[0] if args else cfg.get("default_doc_type")
    topic = args[1] if len(args) > 1 else cfg.get("default_topic")
    if doc_type is None:
        click.echo("Document type required")
        return
    try:
        edit_prompt_inline(doc_type, topic)
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _repl_new_doc_type(args: list[str]) -> None:
    """Create a new document type directory with template prompts."""
    if _REPL_CTX is None:
        click.echo("Document type creation unavailable.")
        return
    from . import new_doc_type as new_doc_type_mod

    name = args[0] if args else None
    try:
        new_doc_type_mod.doc_type(cast(typer.Context, _REPL_CTX), name)
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _repl_delete_doc_type(args: list[str]) -> None:
    """Delete an existing document type directory."""
    if _REPL_CTX is None:
        click.echo("Document type deletion unavailable.")
        return
    from . import new_doc_type as new_doc_type_mod

    name = args[0] if args else None
    try:
        new_doc_type_mod.delete_doc_type(cast(typer.Context, _REPL_CTX), name)
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _repl_rename_doc_type(args: list[str]) -> None:
    """Rename an existing document type."""
    if _REPL_CTX is None:
        click.echo("Document type renaming unavailable.")
        return
    from . import new_doc_type as new_doc_type_mod

    if not args:
        click.echo("New document type name required")
        return
    new = args[0]
    old = args[1] if len(args) > 1 else None
    try:
        new_doc_type_mod.rename_doc_type(cast(typer.Context, _REPL_CTX), new, old=old)
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _repl_duplicate_doc_type(args: list[str]) -> None:
    """Duplicate an existing document type."""
    if _REPL_CTX is None:
        click.echo("Document type duplication unavailable.")
        return
    from . import new_doc_type as new_doc_type_mod

    if not args:
        click.echo("New document type name required")
        return
    new = args[0]
    old = args[1] if len(args) > 1 else None
    try:
        new_doc_type_mod.duplicate_doc_type(cast(typer.Context, _REPL_CTX), new, old=old)
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _repl_new_topic(args: list[str]) -> None:
    """Create a new topic prompt for a document type."""
    if _REPL_CTX is None:
        click.echo("Topic creation unavailable.")
        return
    from . import new_topic as new_topic_mod

    doc_type = args[0] if args else None
    topic = args[1] if len(args) > 1 else None
    try:
        new_topic_mod.topic(cast(typer.Context, _REPL_CTX), topic, doc_type=doc_type)
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _repl_delete_topic(args: list[str]) -> None:
    """Delete a topic prompt from a document type."""
    if _REPL_CTX is None:
        click.echo("Topic deletion unavailable.")
        return
    from . import new_topic as new_topic_mod

    doc_type = args[0] if args else None
    topic = args[1] if len(args) > 1 else None
    try:
        new_topic_mod.delete_topic(
            cast(typer.Context, _REPL_CTX), topic, doc_type=doc_type
        )
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _repl_rename_topic(args: list[str]) -> None:
    """Rename an existing topic prompt for a document type."""
    if _REPL_CTX is None:
        click.echo("Topic renaming unavailable.")
        return
    from . import new_topic as new_topic_mod

    doc_type = args[0] if args else None
    old = args[1] if len(args) > 1 else None
    new = args[2] if len(args) > 2 else None
    try:
        new_topic_mod.rename_topic(
            cast(typer.Context, _REPL_CTX), old, new, doc_type=doc_type
        )
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _repl_duplicate_topic(args: list[str]) -> None:
    """Duplicate a topic prompt for a document type."""
    if _REPL_CTX is None:
        click.echo("Topic duplication unavailable.")
        return
    from . import new_topic as new_topic_mod

    doc_type = args[0] if args else None
    old = args[1] if len(args) > 1 else None
    new = args[2] if len(args) > 2 else None
    try:
        new_topic_mod.duplicate_topic(
            cast(typer.Context, _REPL_CTX), old, new, doc_type=doc_type
        )
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _repl_urls(args: list[str]) -> None:
    """Invoke the URL management command from the REPL."""
    if _REPL_CTX is None:
        click.echo("URL management unavailable.")
        return
    from . import manage_urls as manage_urls_mod

    doc_type = args[0] if args else None
    try:
        manage_urls_mod.manage_urls(cast(typer.Context, _REPL_CTX), doc_type)
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _repl_edit_url_list(args: list[str]) -> None:
    """Edit the stored URL list for a document type."""
    if _REPL_CTX is None:
        click.echo("URL editing unavailable.")
        return
    from . import manage_urls as manage_urls_mod

    doc_types, _ = discover_doc_types_topics()
    doc_type = args[0] if args else None
    if doc_type is None:
        if not doc_types:
            click.echo("No document types available.")
            return
        try:
            doc_type = questionary.select("Document type", choices=doc_types).ask()
        except Exception:
            doc_type = None
    if not doc_type:
        click.echo("Document type required")
        return
    path, urls = manage_urls_mod._load_urls(doc_type)
    initial = "\n".join(urls) + ("\n" if urls else "")
    edited = click.edit(initial)
    if edited is None:
        return
    new_urls: list[str] = []
    for entry in edited.split():
        entry = entry.strip()
        if not manage_urls_mod._valid_url(entry):
            click.echo(f"Skipping invalid URL: {entry}")
            continue
        if entry not in new_urls:
            new_urls.append(entry)
    manage_urls_mod.save_urls(path, new_urls)
    refresh_completer()


def _wizard_new_doc_type() -> None:
    """Wizard to create a new document type."""
    if _REPL_CTX is None:
        click.echo("Wizard unavailable.")
        return
    answers = None
    try:
        answers = questionary.form(
            name=questionary.text("Document type"),
            description=questionary.text("Description", default=""),
        ).ask()
    except Exception:
        answers = None
    if not answers or not answers.get("name"):
        return
    from . import new_doc_type as new_doc_type_mod

    new_doc_type_mod.doc_type(
        cast(typer.Context, _REPL_CTX),
        answers["name"],
        description=answers.get("description", ""),
    )


def _wizard_new_topic() -> None:
    """Wizard to create a new topic for an existing document type."""
    if _REPL_CTX is None:
        click.echo("Wizard unavailable.")
        return
    doc_types, _ = discover_doc_types_topics()
    if not doc_types:
        click.echo("No document types available.")
        return
    answers = None
    try:
        answers = questionary.form(
            doc_type=questionary.select("Document type", choices=doc_types),
            topic=questionary.text("Topic"),
            description=questionary.text("Description", default=""),
        ).ask()
    except Exception:
        answers = None
    if not answers or not answers.get("doc_type") or not answers.get("topic"):
        return
    from . import new_topic as new_topic_mod

    new_topic_mod.topic(
        cast(typer.Context, _REPL_CTX),
        answers["topic"],
        doc_type=answers["doc_type"],
        description=answers.get("description", ""),
    )


def _wizard_urls() -> None:
    """Wizard to bulk add URLs for a document type."""
    if _REPL_CTX is None:
        click.echo("Wizard unavailable.")
        return
    doc_types, _ = discover_doc_types_topics()
    if not doc_types:
        click.echo("No document types available.")
        return
    answers = None
    try:
        answers = questionary.form(
            doc_type=questionary.select("Document type", choices=doc_types),
            urls=questionary.text("Enter URL(s) (one per line)", multiline=True),
        ).ask()
    except Exception:
        answers = None
    if not answers or not answers.get("doc_type") or not answers.get("urls"):
        return
    from . import manage_urls as manage_urls_mod

    path, existing = manage_urls_mod._load_urls(answers["doc_type"])
    new_urls = existing[:]
    for entry in answers["urls"].split():
        entry = entry.strip()
        if not manage_urls_mod._valid_url(entry):
            click.echo(f"Skipping invalid URL: {entry}")
            continue
        if entry not in new_urls:
            new_urls.append(entry)
    manage_urls_mod.save_urls(path, new_urls)
    refresh_completer()


def _repl_wizard(args: list[str]) -> None:
    """Dispatch to interactive wizards."""
    if not args:
        click.echo("Available wizards: new-doc-type, new-topic, urls")
        return
    cmd = args[0]
    if cmd == "new-doc-type":
        _wizard_new_doc_type()
    elif cmd == "new-topic":
        _wizard_new_topic()
    elif cmd == "urls":
        _wizard_urls()
    else:
        click.echo(f"Unknown wizard: {cmd}")


def _repl_set_default(args: list[str]) -> None:
    """Set default document type and optional topic."""
    if _REPL_CTX is None:
        click.echo("Setting defaults unavailable.")
        return
    from .config import default_doc_type, default_topic

    cfg = _REPL_CTX.obj.get("config", {}) if _REPL_CTX.obj else {}
    if not args:
        dt = cfg.get("default_doc_type") or "(none)"
        tp = cfg.get("default_topic") or "(none)"
        click.echo(f"Default document type: {dt}\nDefault topic: {tp}")
        return

    doc_type = None if args[0] == "-" else args[0]
    topic = (
        None
        if len(args) > 1 and args[1] == "-"
        else (args[1] if len(args) > 1 else None)
    )
    default_doc_type(cast(typer.Context, _REPL_CTX), doc_type)
    if len(args) > 1:
        default_topic(cast(typer.Context, _REPL_CTX), topic)


def _repl_doc_types(args: list[str]) -> None:
    """List available document types."""

    doc_types, _ = discover_doc_types_topics()
    for name in doc_types:
        click.echo(name)


def _repl_topics(args: list[str]) -> None:
    """List available analysis topics."""

    _, topics = discover_doc_types_topics()
    for name in topics:
        click.echo(name)


def _register_repl_commands(ctx: click.Context) -> None:
    """Register built-in REPL commands for the given context."""

    global _REPL_CTX
    _REPL_CTX = ctx
    plugins.register_repl_command(":help", _repl_help)
    plugins.register_repl_command(":reload", _repl_reload)
    plugins.register_repl_command(":history", _repl_history)
    plugins.register_repl_command(":clear-history", _repl_clear_history)
    plugins.register_repl_command(":config", _repl_config)
    plugins.register_repl_command(":edit-prompt", _repl_edit_prompt)
    plugins.register_repl_command(":edit-url-list", _repl_edit_url_list)
    plugins.register_repl_command(":urls", _repl_urls)
    plugins.register_repl_command(":manage-urls", _repl_urls)
    plugins.register_repl_command(":wizard", _repl_wizard)
    plugins.register_repl_command(":new-doc-type", _repl_new_doc_type)
    plugins.register_repl_command(":delete-doc-type", _repl_delete_doc_type)
    plugins.register_repl_command(":rename-doc-type", _repl_rename_doc_type)
    plugins.register_repl_command(":duplicate-doc-type", _repl_duplicate_doc_type)
    plugins.register_repl_command(":new-topic", _repl_new_topic)
    plugins.register_repl_command(":rename-topic", _repl_rename_topic)
    plugins.register_repl_command(":delete-topic", _repl_delete_topic)
    plugins.register_repl_command(":duplicate-topic", _repl_duplicate_topic)
    plugins.register_repl_command(":doc-types", _repl_doc_types)
    plugins.register_repl_command(":topics", _repl_topics)
    plugins.register_repl_command(":set-default", _repl_set_default)


def discover_topics(doc_type: str, data_dir: Path = Path("data")) -> list[str]:
    """Return sorted topics available under *doc_type* in ``data_dir``."""

    topics: set[str] = set()
    doc_dir = data_dir / doc_type
    if not doc_dir.exists():
        return []
    for p in doc_dir.glob("analysis_*.prompt.yaml"):
        m = re.match(r"analysis_(.+)\.prompt\.yaml$", p.name)
        if m:
            topics.add(m.group(1))
    for p in doc_dir.glob(f"{doc_type}.analysis.*.prompt.yaml"):
        m = re.match(rf"{re.escape(doc_type)}\.analysis\.(.+)\.prompt\.yaml$", p.name)
        if m:
            topics.add(m.group(1))
    return sorted(topics)


def discover_doc_types_topics(
    data_dir: Path = Path("data"),
) -> tuple[list[str], list[str]]:
    """Return sorted document types and analysis topics under ``data_dir``."""

    if not data_dir.exists():
        return [], []
    doc_types = [p.name for p in data_dir.iterdir() if p.is_dir()]
    topics: set[str] = set()
    for dtype in doc_types:
        topics.update(discover_topics(dtype, data_dir))
    return sorted(doc_types), sorted(topics)


class DocAICompleter(Completer):
    """Completer that hides sensitive env vars and suggests doc types/topics."""

    def __init__(self, cli: Command, ctx: click.Context) -> None:
        self._click = ClickCompleter(cli, ctx)
        self._env = WordCompleter([], ignore_case=True)
        self._doc_types = WordCompleter([], ignore_case=True)
        self._topics = WordCompleter([], ignore_case=True)
        self._ctx = ctx
        self.refresh()

    def refresh(self) -> None:
        """Refresh cached doc types, topics, and environment variables."""
        from . import read_configs  # local import to avoid circular

        cfg: dict[str, str] = {}
        try:
            _, _, merged = read_configs()
            cfg = dict(merged)
        except Exception:
            cfg = {}
        if self._ctx.obj and isinstance(self._ctx.obj.get("config"), dict):
            cfg.update(self._ctx.obj["config"])
        if SAFE_ENV_VARS_ENV in cfg:
            raw: str | None = str(cfg[SAFE_ENV_VARS_ENV])
        elif SAFE_ENV_VARS_ENV in os.environ:
            raw = os.environ[SAFE_ENV_VARS_ENV]
        else:
            raw = None
        allow, deny = _parse_allow_deny(raw)
        exposed = [name for name in os.environ if name in allow and name not in deny]
        env_words = [f"${name}" for name in exposed]
        self._env = WordCompleter(env_words, ignore_case=True)

        doc_types, topics = discover_doc_types_topics(Path("data"))
        default_doc_type = cfg.get("default_doc_type")
        default_topic = cfg.get("default_topic")
        if default_doc_type in doc_types:
            doc_types = [default_doc_type] + [
                d for d in doc_types if d != default_doc_type
            ]
        if default_topic in topics:
            topics = [default_topic] + [t for t in topics if t != default_topic]
        self._doc_types = WordCompleter(doc_types, ignore_case=True)
        self._topics = WordCompleter(topics, ignore_case=True)

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        text = document.text_before_cursor
        if text.startswith("$"):
            yield from self._env.get_completions(document, complete_event)
            return

        parts = text.split()
        if parts:
            cmd = parts[0]
            if cmd == "pipeline":
                if len(parts) == 1 and text.endswith(" "):
                    yield from self._doc_types.get_completions(
                        Document(""), complete_event
                    )
                    return
                if len(parts) == 2 and not parts[1].startswith("-"):
                    yield from self._doc_types.get_completions(
                        Document(parts[1]), complete_event
                    )
                    return
            if "--topic" in parts or "-t" in parts:
                if parts[-1] in {"--topic", "-t"}:
                    yield from self._topics.get_completions(
                        Document(""), complete_event
                    )
                    return
                if len(parts) >= 2 and parts[-2] in {"--topic", "-t"}:
                    yield from self._topics.get_completions(
                        Document(parts[-1]), complete_event
                    )
                    return
            if cmd == "urls":
                if len(parts) == 1 and text.endswith(" "):
                    yield from self._doc_types.get_completions(
                        Document(""), complete_event
                    )
                    return
                if len(parts) == 2 and not parts[1].startswith("-"):
                    yield from self._doc_types.get_completions(
                        Document(parts[1]), complete_event
                    )
                    return

        yield from self._click.get_completions(document, complete_event)
        for provider in plugins.iter_completion_providers():
            yield from provider(document, complete_event)


def refresh_completer() -> None:
    """Refresh the interactive completer if the REPL is active."""

    comp = PROMPT_KWARGS.get("completer") if PROMPT_KWARGS else None
    if isinstance(comp, DocAICompleter):
        comp.refresh()


F = TypeVar("F", bound=Callable[..., Any])


def refresh_after(func: F) -> F:
    """Decorator to refresh the REPL completer after *func* succeeds."""

    from functools import wraps

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)
        refresh_completer()
        return result

    return cast(F, wrapper)


def _prompt_name() -> str:
    """Return the current directory name for the REPL prompt.

    The repository root directory name ``doc-ai-analysis-starter`` is shortened
    to ``doc-ai`` for a cleaner initial prompt.
    """

    name = Path.cwd().name
    return "doc-ai" if name == "doc-ai-analysis-starter" else name


def interactive_shell(app: typer.Typer, init: Path | None = None) -> None:
    """Start an interactive REPL for the given Typer application.

    If *init* is provided, commands from that file are executed via
    :func:`run_batch` before the prompt is shown.
    """

    cmd = get_command(app)
    ctx = click.Context(cmd)
    _register_repl_commands(ctx)

    from . import read_configs  # local import

    global_cfg, _env_vals, merged = read_configs()
    ctx.obj = {"global_config": global_cfg, "config": merged, "interactive": True}

    if _allow_shell_from_config(merged):
        warnings.warn(
            f"Shell escapes enabled via {ALLOW_SHELL_ENV}; use with caution.",
            stacklevel=1,
        )

    if init is not None:
        try:
            run_batch(ctx, init)
        except typer.Exit:
            raise
        except Exception:
            logger.exception("Failed to run batch file %s", init)

    hist_raw = str(
        merged.get(HISTORY_FILE_ENV) or os.getenv(HISTORY_FILE_ENV, "")
    ).strip()
    history: FileHistory | None = None
    history_path: Path | None
    if hist_raw == "-":
        history_path = None
    else:
        if hist_raw:
            history_path = Path(hist_raw).expanduser()
        else:
            dirs = PlatformDirs("doc_ai")
            data_dir = dirs.user_data_path
            data_dir.mkdir(parents=True, exist_ok=True)
            if os.name != "nt":
                try:
                    data_dir.chmod(0o700)
                except OSError:
                    pass
            history_path = data_dir / "history"
        exists = history_path.exists()
        history_path.touch(mode=0o600, exist_ok=True)
        if os.name != "nt":
            if exists:
                try:
                    history_path.chmod(0o600)
                except OSError:
                    pass
        else:
            try:
                mode = history_path.stat().st_mode
                if os.access(history_path, os.R_OK) and mode & (
                    stat.S_IRGRP | stat.S_IROTH
                ):
                    warnings.warn("History file is world-readable.")
            except OSError:
                pass
        history = FileHistory(history_path)

    global PROMPT_KWARGS
    PROMPT_KWARGS = {
        "message": lambda: f"{_prompt_name()}>",
        "completer": DocAICompleter(cmd, ctx),
    }
    if history is not None:
        PROMPT_KWARGS["history"] = history

    repl(ctx, prompt_kwargs=PROMPT_KWARGS)
