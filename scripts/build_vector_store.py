import argparse
import json
from pathlib import Path
from openai import OpenAI

def build_vector_store(docs_dir: Path, out_dir: Path, model: str) -> None:
    """Generate embeddings for Markdown files and save to a JSON store."""
    client = OpenAI()
    out_dir.mkdir(parents=True, exist_ok=True)
    store = {}
    for md_file in sorted(docs_dir.rglob("*.md")):
        text = md_file.read_text()
        response = client.embeddings.create(model=model, input=text)
        store[md_file.name] = response.data[0].embedding
    (out_dir / "embeddings.json").write_text(json.dumps(store) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("docs", type=Path, help="Directory containing markdown documents")
    parser.add_argument("--outdir", type=Path, default=Path("vector_store"))
    parser.add_argument("--model", default="text-embedding-3-small")
    args = parser.parse_args()
    build_vector_store(args.docs, args.outdir, args.model)
