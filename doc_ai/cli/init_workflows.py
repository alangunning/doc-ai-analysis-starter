from __future__ import annotations

import shutil
from pathlib import Path
import typer

app = typer.Typer(invoke_without_command=True, help="Copy GitHub Actions workflow templates into a project.")

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / ".github" / "workflows"


@app.callback()
def init_workflows(
    dest: Path = typer.Option(
        Path(".github/workflows"), "--dest", help="Target directory for workflows"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing files"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show actions without writing files"
    ),
) -> None:
    """Copy workflow templates into ``dest``."""
    files = list(TEMPLATE_DIR.glob("*.yml")) + list(TEMPLATE_DIR.glob("*.yaml"))
    if not files:
        typer.echo("No workflow templates found", err=True)
        raise typer.Exit(1)
    dest.mkdir(parents=True, exist_ok=True)
    for src in files:
        target = dest / src.name
        if target.exists() and not overwrite:
            typer.echo(f"Skipping {target} (exists). Use --overwrite to replace.")
            continue
        if dry_run:
            typer.echo(f"Would copy {src} -> {target}")
        else:
            shutil.copy2(src, target)
            typer.echo(f"Copied {src.name}")
