# mypy: ignore-errors
"""Interactive REPL helper for the Doc AI CLI."""

from __future__ import annotations

from pathlib import Path
import os
import re
import stat
import warnings
from platformdirs import PlatformDirs

import click
from click_repl import repl, ClickCompleter
from doc_ai import plugins
from click.exceptions import Exit as ClickExit
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, WordCompleter
from prompt_toolkit.document import Document
import typer
from typer.main import get_command
from doc_ai.batch import run_batch


SAFE_ENV_VARS_ENV = "DOC_AI_SAFE_ENV_VARS"
"""Config key with comma-separated allow/deny env var names."""

SAFE_ENV_VARS: set[str] = {"PATH", "HOME"}
"""Base names of environment variables that may be exposed in the REPL."""


def _parse_allow_deny(value: str) -> tuple[set[str], set[str]]:
    """Return allow and deny sets parsed from a comma-separated *value*.

    Items prefixed with ``-`` are placed in the deny set; all others are
    considered allowed. Empty items are ignored. ``+`` prefixes are optional and
    treated the same as no prefix.
    """

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

__all__ = [
    "interactive_shell",
    "run_batch",
    "DocAICompleter",
    "discover_doc_types_topics",
    "SAFE_ENV_VARS",
    "PROMPT_KWARGS",
    "refresh_completer",
    "refresh_after",
    "_prompt_name",
]


def _repl_help(args: list[str]) -> None:
    """Display help for CLI commands or the REPL itself."""

    if _REPL_CTX is None:
        click.echo("Help is unavailable.")
        return

    ctx = _REPL_CTX
    cmd = ctx.command
    cur_ctx = ctx
    path: list[str] = []
    for arg in args:
        if isinstance(cmd, click.MultiCommand):
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
    elif isinstance(cmd, click.MultiCommand):
        subs = sorted(cmd.list_commands(cur_ctx))
        if subs:
            click.echo("\nSubcommands: " + ", ".join(subs))
            click.echo(f"Example: :help {' '.join(path + [subs[0]])}")
    else:
        example = " ".join(path or [cmd.name]) + " --help"
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


def _repl_edit_prompt(args: list[str]) -> None:
    """Edit prompt for the current or given doc type/topic."""
    if _REPL_CTX is None:
        click.echo("Prompt editing unavailable.")
        return
    from .prompt import edit_prompt

    cfg = _REPL_CTX.obj.get("config", {}) if _REPL_CTX.obj else {}
    doc_type = args[0] if args else cfg.get("default_doc_type")
    topic = args[1] if len(args) > 1 else cfg.get("default_topic")
    if doc_type is None:
        click.echo("Document type required")
        return
    try:
        edit_prompt(doc_type, topic)
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
        new_doc_type_mod.doc_type(_REPL_CTX, name)
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
        new_doc_type_mod.rename_doc_type(_REPL_CTX, new, old=old)
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
        new_topic_mod.topic(_REPL_CTX, topic, doc_type=doc_type)
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
        new_topic_mod.rename_topic(_REPL_CTX, old, new, doc_type=doc_type)
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
        manage_urls_mod.manage_urls(_REPL_CTX, doc_type)
    except click.ClickException as exc:
        click.echo(exc.format_message())


def _register_repl_commands(ctx: click.Context) -> None:
    """Register built-in REPL commands for the given context."""

    global _REPL_CTX
    _REPL_CTX = ctx
    plugins.register_repl_command(":help", _repl_help)
    plugins.register_repl_command(":reload", _repl_reload)
    plugins.register_repl_command(":history", _repl_history)
    plugins.register_repl_command(":config", _repl_config)
    plugins.register_repl_command(":edit-prompt", _repl_edit_prompt)
    plugins.register_repl_command(":urls", _repl_urls)
    plugins.register_repl_command(":manage-urls", _repl_urls)
    plugins.register_repl_command(":new-doc-type", _repl_new_doc_type)
    plugins.register_repl_command(":rename-doc-type", _repl_rename_doc_type)
    plugins.register_repl_command(":new-topic", _repl_new_topic)
    plugins.register_repl_command(":rename-topic", _repl_rename_topic)


def discover_doc_types_topics(
    data_dir: Path = Path("data"),
) -> tuple[list[str], list[str]]:
    """Return sorted document types and analysis topics under ``data_dir``.

    This mirrors the discovery used by :class:`DocAICompleter` so other
    commands can enumerate the same resources without duplicating logic.
    """

    if not data_dir.exists():
        return [], []
    doc_types = [p.name for p in data_dir.iterdir() if p.is_dir()]
    topics: set[str] = set()
    for dtype in doc_types:
        doc_dir = data_dir / dtype
        for p in doc_dir.glob("analysis_*.prompt.yaml"):
            m = re.match(r"analysis_(.+)\.prompt\.yaml$", p.name)
            if m:
                topics.add(m.group(1))
        for p in doc_dir.glob(f"{dtype}.analysis.*.prompt.yaml"):
            m = re.match(rf"{re.escape(dtype)}\.analysis\.(.+)\.prompt\.yaml$", p.name)
            if m:
                topics.add(m.group(1))
    return sorted(doc_types), sorted(topics)


class DocAICompleter(Completer):
    """Completer that hides sensitive env vars and suggests doc types/topics."""

    def __init__(self, cli: click.BaseCommand, ctx: click.Context) -> None:
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
        raw = cfg.get(SAFE_ENV_VARS_ENV, "") or os.getenv(SAFE_ENV_VARS_ENV, "")
        allow, deny = _parse_allow_deny(raw)
        allowed = SAFE_ENV_VARS.union(allow)

        exposed = [name for name in os.environ if name in allowed and name not in deny]
        if not raw and len(exposed) > 5:
            warnings.warn(
                f"{SAFE_ENV_VARS_ENV} is unset; completions will expose many environment variables.",
                stacklevel=1,
            )
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

    def get_completions(self, document, complete_event=None):  # type: ignore[override]
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


def refresh_after(func):
    """Decorator to refresh the REPL completer after *func* succeeds."""

    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        refresh_completer()
        return result

    return wrapper




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
    if init is not None:
        run_batch(ctx, init)
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
            if os.access(history_path, os.R_OK) and mode & (stat.S_IRGRP | stat.S_IROTH):
                warnings.warn("History file is world-readable.")
        except OSError:
            pass
    history = FileHistory(history_path)
    global PROMPT_KWARGS
    PROMPT_KWARGS = {
        "history": history,
        "message": lambda: f"{_prompt_name()}>",
        "completer": DocAICompleter(cmd, ctx),
    }
    repl(ctx, prompt_kwargs=PROMPT_KWARGS)
