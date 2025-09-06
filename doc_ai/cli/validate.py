from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from doc_ai.converter import OutputFormat

from . import ModelName, _validate_prompt
from .utils import (
    infer_format as _infer_format,
)
from .utils import (
    prompt_if_missing,
    resolve_bool,
    resolve_str,
    validate_doc,
)
from .utils import (
    suffix as _suffix,
)

app = typer.Typer(
    invoke_without_command=True,
    help="Validate converted output against the original file.",
)


@app.callback()
def validate(
    ctx: typer.Context,
    raw: Path | None = typer.Argument(None, help="Path to raw document"),
    rendered: Path | None = typer.Argument(None, help="Path to converted file"),
    fmt: Optional[OutputFormat] = typer.Option(None, "--format", "-f"),
    prompt: Optional[Path] = typer.Option(
        None,
        "--prompt",
        help="Prompt file (overrides auto-detected *.validate.prompt.yaml)",
        callback=_validate_prompt,
    ),
    model: Optional[ModelName] = typer.Option(
        None,
        "--model",
        help="Model name override",
    ),
    base_model_url: Optional[str] = typer.Option(
        None,
        "--base-model-url",
        help="Model base URL override",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Re-run validation even if metadata is present",
        is_flag=True,
    ),
) -> None:
    """Validate converted output against the original file.

    Examples:
        doc-ai validate report.pdf
    """
    if ctx.obj is None:
        ctx.obj = {}

    cfg = ctx.obj.get("config", {})
    raw_val = prompt_if_missing(
        ctx, str(raw) if raw is not None else None, "Path to raw document"
    )
    if raw_val is None:
        raise typer.BadParameter("Missing argument 'raw'")
    raw = Path(raw_val)
    model_name = resolve_str(
        ctx, "model", model.value if model else None, cfg, "VALIDATE_MODEL"
    )
    model = ModelName(model_name) if model_name is not None else None
    base_model_url = resolve_str(
        ctx, "base_model_url", base_model_url, cfg, "VALIDATE_BASE_MODEL_URL"
    )
    force = resolve_bool(ctx, "force", force, cfg, "FORCE")

    console_local = Console()
    if rendered is None:
        used_fmt = fmt or OutputFormat.MARKDOWN
        rendered = raw.with_name(raw.name + _suffix(used_fmt))
    else:
        used_fmt = fmt or _infer_format(rendered)

    validate_doc(
        raw,
        rendered,
        used_fmt,
        prompt,
        model,
        base_model_url,
        show_progress=True,
        console=console_local,
        force=force,
    )
