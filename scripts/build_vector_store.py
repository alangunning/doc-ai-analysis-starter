import argparse
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = os.environ.get("EMBED_MODEL", "openai/text-embedding-3-small")
EMBED_DIMENSIONS = os.environ.get("EMBED_DIMENSIONS")


def build_vectors(src_dir: Path, out_dir: Path) -> None:
    """Generate embeddings for Markdown files using GitHub's Models API."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    api_url = "https://models.github.ai/inference/embeddings"
    out_dir.mkdir(parents=True, exist_ok=True)

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
        out_file = out_dir / (md_file.stem + ".json")
        out_file.write_text(
            json.dumps({"file": str(md_file), "embedding": embedding}) + "\n",
            encoding="utf-8",
        )

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path, help="Directory of Markdown files")
    p.add_argument("outdir", type=Path, help="Output directory for vector store")
    args = p.parse_args()
    build_vectors(args.source, args.outdir)
