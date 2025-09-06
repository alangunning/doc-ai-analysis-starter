"""Interactive REPL helper for the Doc AI CLI."""

from __future__ import annotations

from pathlib import Path
import os
import re
from platformdirs import PlatformDirs

import click
from click_repl import repl, ClickCompleter
from click_repl.utils import (
    dispatch_repl_commands,
    handle_internal_commands,
    split_arg_string,
)
from click_repl.exceptions import CommandLineParserError
from click.exceptions import Exit as ClickExit
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, WordCompleter
from prompt_toolkit.document import Document
import typer
from typer.main import get_command


SAFE_ENV_VARS_ENV = "DOC_AI_SAFE_ENV_VARS"
"""Environment variable containing comma-separated safe env var names."""

SAFE_ENV_VARS = {
    v.strip() for v in os.getenv(SAFE_ENV_VARS_ENV, "").split(",") if v.strip()
}
"""Names of environment variables that may be exposed in the REPL."""

PROMPT_KWARGS: dict[str, object] | None = None

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
        self.refresh()

    def refresh(self) -> None:
        """Refresh cached doc types, topics, and environment variables."""

        pattern = re.compile(r"TOKEN|SECRET|PASSWORD|APIKEY|API_KEY|KEY", re.IGNORECASE)
        allowed = SAFE_ENV_VARS.union(
            {
                v.strip()
                for v in os.getenv(SAFE_ENV_VARS_ENV, "").split(",")
                if v.strip()
            }
        )
        env_words = [
            f"${name}"
            for name in os.environ
            if name in allowed or not pattern.search(name)
        ]
        self._env = WordCompleter(env_words, ignore_case=True)

        doc_types, topics = discover_doc_types_topics(Path("data"))
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
            if cmd == "add" and len(parts) >= 2 and parts[1] == "manage-urls":
                if len(parts) == 2 and text.endswith(" "):
                    yield from self._doc_types.get_completions(
                        Document(""), complete_event
                    )
                    return
                if len(parts) == 3 and not parts[2].startswith("-"):
                    yield from self._doc_types.get_completions(
                        Document(parts[2]), complete_event
                    )
                    return

        yield from self._click.get_completions(document, complete_event)


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


def _parse_command(command: str) -> list[str] | None:
    """Parse a command line similar to click-repl's REPL parser."""
    if dispatch_repl_commands(command):
        return None
    result = handle_internal_commands(command)
    if isinstance(result, str):
        click.echo(result)
        return None
    try:
        parts = split_arg_string(command, posix=False)
        cleaned = []
        for part in parts:
            if len(part) >= 2 and part[0] == part[-1] and part[0] in {'"', "'"}:
                cleaned.append(part[1:-1])
            else:
                cleaned.append(part)
        return cleaned
    except ValueError as exc:  # pragma: no cover - handled by caller
        raise CommandLineParserError(str(exc)) from exc


def run_batch(ctx: click.Context, path: Path) -> None:
    """Execute commands from *path* before starting the REPL."""
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        args = _parse_command(line)
        if args is None:
            continue
        sub_ctx = ctx.command.make_context(
            ctx.command.name,
            args,
            obj=ctx.obj,
            default_map=ctx.default_map,
        )
        try:
            ctx.command.invoke(sub_ctx)
        except click.ClickException:
            raise
        except ClickExit as exc:
            raise typer.Exit(exc.exit_code)
        finally:
            ctx.default_map = sub_ctx.default_map


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
    if init is not None:
        run_batch(ctx, init)
    dirs = PlatformDirs("doc_ai")
    data_dir = dirs.user_data_path
    data_dir.mkdir(parents=True, exist_ok=True)
    data_dir.chmod(0o700)
    history_path = data_dir / "history"
    exists = history_path.exists()
    history_path.touch(mode=0o600, exist_ok=True)
    if exists:
        history_path.chmod(0o600)
    history = FileHistory(history_path)
    global PROMPT_KWARGS
    PROMPT_KWARGS = {
        "history": history,
        "message": lambda: f"{_prompt_name()}>",
        "completer": DocAICompleter(cmd, ctx),
    }
    repl(ctx, prompt_kwargs=PROMPT_KWARGS)
