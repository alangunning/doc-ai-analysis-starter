from __future__ import annotations

import typer

from doc_ai.converter import OutputFormat
from .import_cmd import process_urls

app = typer.Typer(help="Add resources to the project.")


@app.command("url")
def add_url(
    link: str = typer.Argument(..., help="Remote document URL"),
    doc_type: str = typer.Option(
        ..., "--doc-type", help="Document type directory under data/."
    ),
) -> None:
    """Download and convert a document from a URL."""
    process_urls([link], doc_type, [OutputFormat.MARKDOWN])
