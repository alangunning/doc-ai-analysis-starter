from __future__ import annotations

import json
import math
import os
from pathlib import Path

import typer
from openai import OpenAI

from doc_ai.github.prompts import DEFAULT_MODEL_BASE_URL
from doc_ai.github.vector import EMBED_MODEL
from doc_ai.openai import create_response

from . import ModelName
from .utils import prompt_if_missing, resolve_bool, resolve_str

app = typer.Typer(
    invoke_without_command=True, help="Query a vector store for similar documents."
)


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
    store: Path | None = typer.Argument(
        None, help="Directory containing .embedding.json files", file_okay=False
    ),
    text: str | None = typer.Argument(None, help="Query text"),
    k: int = typer.Option(5, "--k", help="Number of matches to display"),
    ask: bool = typer.Option(
        False,
        "--ask",
        help="Send top matches to an LLM and return an answer",
        is_flag=True,
    ),
    model: ModelName = typer.Option(
        ModelName.GPT_4O_MINI,
        "--model",
        help="Model to use when answering with --ask",
    ),
) -> None:
    """Run a similarity search against embeddings in ``store``."""
    if ctx.obj is None:
        ctx.obj = {}

    cfg = ctx.obj.get("config", {})
    store_val = prompt_if_missing(
        ctx,
        str(store) if store is not None else None,
        "Directory containing .embedding.json files",
    )
    if store_val is None:
        raise typer.BadParameter("Missing argument 'store'")
    store = Path(store_val)
    text = prompt_if_missing(ctx, text, "Query text")
    if text is None:
        raise typer.BadParameter("Missing argument 'text'")
    ask = resolve_bool(ctx, "ask", ask, cfg, "ASK")
    model_name = resolve_str(ctx, "model", model.value, cfg, "MODEL")
    try:
        model = ModelName(model_name)
    except ValueError as exc:
        raise typer.BadParameter(f"Invalid model '{model_name}'") from exc

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
    top_docs: list[tuple[str, str]] = []
    for score, fname in results[:k]:
        typer.echo(f"{score:.4f}\t{fname}")
        if ask:
            try:
                content = Path(fname).read_text(encoding="utf-8")
            except Exception:  # pragma: no cover - best effort
                content = ""
            top_docs.append((fname, content))

    if ask and top_docs:
        parts = ["Use the following documents to answer the question:"]
        for idx, (fname, content) in enumerate(top_docs, 1):
            parts.append(f"Document {idx}: {fname}\n{content}")
        parts.append(f"Question: {text}\nAnswer:")
        prompt = "\n\n".join(parts)
        resp = create_response(
            client,
            model=model.value,
            texts=prompt,
        )
        answer = getattr(resp, "output_text", "").strip()
        if answer:
            typer.echo(f"\n{answer}\n")
            typer.echo("References:")
            for fname, _ in top_docs:
                typer.echo(f"- {fname}")
