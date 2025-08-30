import argparse
from pathlib import Path

from dotenv import load_dotenv
from docling.document_converter import DocumentConverter

load_dotenv()

def convert(input_path: Path, output_path: Path) -> None:
    converter = DocumentConverter()
    md = converter.convert_to_markdown(input_path)
    output_path.write_text(md, encoding="utf-8")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Path to raw document or folder")
    parser.add_argument("--outdir", default="data/markdown", help="Base output directory")
    args = parser.parse_args()

    in_path = Path(args.source)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if in_path.is_file():
        rel = in_path.name
        out_file = out_dir / Path(rel).with_suffix(".md")
        convert(in_path, out_file)
    else:
        for file in in_path.rglob("*"):
            if file.is_file():
                rel = file.relative_to(in_path)
                out_file = out_dir / rel.with_suffix(".md")
                out_file.parent.mkdir(parents=True, exist_ok=True)
                convert(file, out_file)
