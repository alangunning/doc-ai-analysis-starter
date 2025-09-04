from __future__ import annotations

from pathlib import Path
import warnings

import typer

from doc_ai.converter import OutputFormat
from .utils import parse_env_formats as _parse_env_formats
from . import SETTINGS, console

app = typer.Typer(invoke_without_command=True, help="Convert files using Docling.")


@app.callback()
def convert(
    source: str = typer.Argument(
        ..., help="Path or URL to raw document or folder"
    ),
    format: list[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Desired output format(s). Can be passed multiple times.",
    ),
) -> None:
    """Convert files using Docling."""
    from . import convert_path as _convert_path
    fmts = format or _parse_env_formats() or [OutputFormat.MARKDOWN]
    if not SETTINGS["verbose"]:
        warnings.filterwarnings("ignore")
    if source.startswith(("http://", "https://")):
        results = _convert_path(source, fmts)
    else:
        results = _convert_path(Path(source), fmts)
    if not results:
        console.print("No new files to process.")
