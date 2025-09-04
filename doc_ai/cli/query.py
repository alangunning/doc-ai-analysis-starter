from __future__ import annotations

import json
import math
import os
from pathlib import Path
import logging

import typer
from openai import OpenAI

from doc_ai.github.vector import EMBED_MODEL
from doc_ai.github.prompts import DEFAULT_MODEL_BASE_URL
from doc_ai.logging import configure_logging

app = typer.Typer(invoke_without_command=True, help="Query a vector store for similar documents.")


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Return cosine similarity between two vectors."""
    if not a or not b:
        return 0.0
    num = sum(x * y for x, y in zip(a, b))
    den_a = math.sqrt(sum(x * x for x in a))
    den_b = math.sqrt(sum(y * y for y in b))
    denom = den_a * den_b
    return num / denom if denom else 0.0


@app.callback()
def query(
    ctx: typer.Context,
    store: Path = typer.Argument(
        ..., help="Directory containing .embedding.json files", file_okay=False
    ),
    text: str = typer.Argument(..., help="Query text"),
    k: int = typer.Option(5, "--k", help="Number of matches to display"),
    verbose: bool | None = typer.Option(
        None, "--verbose", "-v", help="Shortcut for --log-level DEBUG"
    ),
    log_level: str | None = typer.Option(
        None, "--log-level", help="Logging level (e.g. INFO, DEBUG)"
    ),
    log_file: Path | None = typer.Option(
        None, "--log-file", help="Write logs to the given file"
    ),
) -> None:
    """Run a similarity search against embeddings in ``store``."""
    if ctx.obj is None:
        ctx.obj = {}
    if any(opt is not None for opt in (verbose, log_level, log_file)):
        level_name = "DEBUG" if verbose else log_level or logging.getLevelName(
            logging.getLogger().level
        )
        configure_logging(level_name, log_file)
        ctx.obj["verbose"] = logging.getLogger().level <= logging.DEBUG
        ctx.obj["log_level"] = level_name
        ctx.obj["log_file"] = log_file

    base_url = (
        os.getenv("VECTOR_BASE_MODEL_URL")
        or os.getenv("BASE_MODEL_URL")
        or DEFAULT_MODEL_BASE_URL
    )
    api_key_var = "OPENAI_API_KEY" if "api.openai.com" in base_url else "GITHUB_TOKEN"
    token = os.getenv(api_key_var)
    if not token:
        raise RuntimeError(f"Missing required environment variable: {api_key_var}")
    client = OpenAI(api_key=token, base_url=base_url)

    resp = client.embeddings.create(
        model=EMBED_MODEL, input=text, encoding_format="float"
    )
    query_vec = resp.data[0].embedding

    results: list[tuple[float, str]] = []
    for emb_file in store.rglob("*.embedding.json"):
        try:
            data = json.loads(emb_file.read_text())
            emb = data["embedding"]
        except Exception:  # pragma: no cover - bad file
            continue
        score = _cosine_similarity(query_vec, emb)
        results.append((score, data.get("file", str(emb_file))))

    results.sort(key=lambda x: x[0], reverse=True)
    for score, fname in results[:k]:
        typer.echo(f"{score:.4f}\t{fname}")
