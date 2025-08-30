import argparse
from pathlib import Path

from dotenv import load_dotenv

from docai import OutputFormat, convert_file, suffix_for_format

load_dotenv()


def convert_directory(source: Path, out_dir: Path, fmt: OutputFormat) -> None:
    if source.is_file():
        rel = source.name
        out_file = out_dir / Path(rel).with_suffix(suffix_for_format(fmt))
        convert_file(source, out_file, fmt)
    else:
        for file in source.rglob("*"):
            if file.is_file():
                rel = file.relative_to(source)
                out_file = out_dir / rel.with_suffix(suffix_for_format(fmt))
                out_file.parent.mkdir(parents=True, exist_ok=True)
                convert_file(file, out_file, fmt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Path to raw document or folder")
    parser.add_argument("--outdir", default="data/markdown", help="Base output directory")
    parser.add_argument(
        "--format",
        default=OutputFormat.MARKDOWN.value,
        choices=[f.value for f in OutputFormat],
        help="Desired output format",
    )
    args = parser.parse_args()

    in_path = Path(args.source)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fmt = OutputFormat(args.format)
    convert_directory(in_path, out_dir, fmt)
