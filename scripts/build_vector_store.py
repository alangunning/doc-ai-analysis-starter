import argparse
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "openai/text-embedding-3-small")
EMBED_DIMENSIONS = os.getenv("EMBED_DIMENSIONS")


def build_vector_store(src_dir: Path) -> None:
    """Generate embeddings for Markdown files in ``src_dir``."""

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")

    api_url = "https://models.github.ai/inference/embeddings"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    for md_file in src_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        payload: dict[str, object] = {
            "model": EMBED_MODEL,
            "input": [text],
            "encoding_format": "float",
        }
        if EMBED_DIMENSIONS:
            payload["dimensions"] = int(EMBED_DIMENSIONS)
        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        embedding = resp.json()["data"][0]["embedding"]
        out_file = md_file.with_suffix(".embedding.json")
        out_file.write_text(
            json.dumps({"file": str(md_file), "embedding": embedding}) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path, help="Directory containing Markdown files")
    args = p.parse_args()
    build_vector_store(args.source)
