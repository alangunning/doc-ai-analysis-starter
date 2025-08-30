import argparse
import json
from pathlib import Path
from openai import OpenAI

EMBED_MODEL = "text-embedding-3-small"

def build_vectors(src_dir: Path, out_dir: Path) -> None:
    client = OpenAI()
    out_dir.mkdir(parents=True, exist_ok=True)
    for md_file in src_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        resp = client.embeddings.create(model=EMBED_MODEL, input=text)
        embedding = resp.data[0].embedding
        out_file = out_dir / (md_file.stem + ".json")
        out_file.write_text(json.dumps({"file": str(md_file), "embedding": embedding}) + "\n", encoding="utf-8")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path, help="Directory of Markdown files")
    p.add_argument("outdir", type=Path, help="Output directory for vector store")
    args = p.parse_args()
    build_vectors(args.source, args.outdir)
