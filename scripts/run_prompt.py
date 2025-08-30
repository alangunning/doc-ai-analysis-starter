import argparse
from pathlib import Path

from docai.prompts import run_prompt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=Path)
    parser.add_argument("markdown_doc", type=Path)
    parser.add_argument("--outdir", default="outputs", type=Path)
    args = parser.parse_args()

    result = run_prompt(args.prompt, args.markdown_doc.read_text())
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / (args.markdown_doc.stem + ".json")).write_text(
        result + "\n", encoding="utf-8"
    )
