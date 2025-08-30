import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from docai import OutputFormat, convert_files, suffix_for_format

load_dotenv()


def convert_directory(source: Path, out_dir: Path, formats: list[OutputFormat]) -> None:
    def handle_file(file: Path) -> None:
        rel = file.name if source.is_file() else file.relative_to(source)
        outputs = {}
        for fmt in formats:
            if len(formats) == 1 and out_dir.name == fmt.value:
                fmt_dir = out_dir
            else:
                fmt_dir = out_dir / fmt.value
            out_path = fmt_dir / Path(rel).with_suffix(suffix_for_format(fmt))
            outputs[fmt] = out_path
        convert_files(file, outputs)

    if source.is_file():
        handle_file(source)
    else:
        for file in source.rglob("*"):
            if file.is_file():
                handle_file(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Path to raw document or folder")
    parser.add_argument("--outdir", default="data/markdown", help="Base output directory")
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        help="Desired output format(s). Can be passed multiple times.\n"
        "If omitted, the OUTPUT_FORMATS environment variable or Markdown is used.",
    )
    args = parser.parse_args()

    in_path = Path(args.source)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def parse_formats(values: list[str]) -> list[OutputFormat]:
        formats: list[OutputFormat] = []
        for val in values:
            try:
                formats.append(OutputFormat(val.strip()))
            except ValueError as exc:  # provide clearer error message
                valid = ", ".join(f.value for f in OutputFormat)
                raise SystemExit(f"Invalid output format '{val}'. Choose from: {valid}") from exc
        return formats

    if args.formats:
        fmts = parse_formats(args.formats)
    elif os.getenv("OUTPUT_FORMATS"):
        fmts = parse_formats(os.getenv("OUTPUT_FORMATS").split(","))
    else:
        fmts = [OutputFormat.MARKDOWN]

    convert_directory(in_path, out_dir, fmts)
