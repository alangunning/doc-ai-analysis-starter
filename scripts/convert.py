import argparse
import os
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Allow running without installing as a package by adding project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from doc_ai.converter import OutputFormat, convert_path


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Path to raw document or folder")
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        help=(
            "Desired output format(s). Can be passed multiple times.\n"
            "If omitted, the OUTPUT_FORMATS environment variable or Markdown is used."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Emit verbose warnings and library output",
    )
    args = parser.parse_args()

    in_path = Path(args.source)

    def parse_formats(values: list[str]) -> list[OutputFormat]:
        formats: list[OutputFormat] = []
        for val in values:
            try:
                formats.append(OutputFormat(val.strip()))
            except ValueError as exc:  # provide clearer error message
                valid = ", ".join(f.value for f in OutputFormat)
                raise SystemExit(
                    f"Invalid output format '{val}'. Choose from: {valid}"
                ) from exc
        return formats

    if not args.verbose:
        warnings.filterwarnings("ignore")

    if args.formats:
        fmts = parse_formats(args.formats)
    elif os.getenv("OUTPUT_FORMATS"):
        fmts = parse_formats(os.getenv("OUTPUT_FORMATS").split(","))
    else:
        fmts = [OutputFormat.MARKDOWN]

    results = convert_path(in_path, fmts)
    if not results:
        print("No new files to process.")
