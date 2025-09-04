from __future__ import annotations

import shutil
from pathlib import Path
import typer

from .utils import resolve_bool, resolve_str

app = typer.Typer(invoke_without_command=True, help="Copy GitHub Actions workflow templates into a project.")

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / ".github" / "workflows"


@app.callback()
def init_workflows(
    ctx: typer.Context,
    dest: Path = typer.Option(
        Path(".github/workflows"), "--dest", help="Target directory for workflows"
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing files (prompt before replacing unless --yes)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show actions without writing files",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Automatic yes to prompts; overwrite without confirmation",
    ),
) -> None:
    """Copy workflow templates into ``dest``."""
    files = list(TEMPLATE_DIR.glob("*.yml")) + list(TEMPLATE_DIR.glob("*.yaml"))
    if not files:
        typer.echo("No workflow templates found", err=True)
        raise typer.Exit(1)
    cfg = ctx.obj.get("config", {})
    dest = Path(resolve_str(ctx, "dest", str(dest), cfg, "DEST"))
    overwrite = resolve_bool(ctx, "overwrite", overwrite, cfg, "OVERWRITE")
    dry_run = resolve_bool(ctx, "dry_run", dry_run, cfg, "DRY_RUN")
    yes = resolve_bool(ctx, "yes", yes, cfg, "YES")
    dest.mkdir(parents=True, exist_ok=True)
    for src in files:
        target = dest / src.name
        if target.exists():
            if not overwrite:
                typer.echo(f"Skipping {target} (exists). Use --overwrite to replace.")
                continue
            if not dry_run and not yes:
                if not typer.confirm(f"{target} exists. Overwrite?", default=False):
                    typer.echo(f"Skipping {target}")
                    continue
        if dry_run:
            typer.echo(f"Would copy {src} -> {target}")
        else:
            shutil.copy2(src, target)
            typer.echo(f"Copied {src.name}")
