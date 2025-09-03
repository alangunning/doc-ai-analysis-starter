import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from doc_ai import OutputFormat, suffix_for_format
from doc_ai.cli import analyze_doc


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Raw or converted document")
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        help="Format of converted file (defaults to markdown)",
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        help="Prompt file (overrides auto-detected *.analysis.prompt.yaml)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file; defaults to <doc>.analysis.json next to the source",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("ANALYZE_MODEL"),
        help="Model name override",
    )
    parser.add_argument(
        "--base-model-url",
        default=os.getenv("ANALYZE_BASE_MODEL_URL")
        or os.getenv("BASE_MODEL_URL"),
        help="Model base URL override",
    )
    args = parser.parse_args()

    doc_path = args.source
    if ".converted" not in "".join(doc_path.suffixes):
        fmt = OutputFormat(args.format) if args.format else OutputFormat.MARKDOWN
        doc_path = doc_path.with_name(
            doc_path.name + f".converted{suffix_for_format(fmt)}"
        )

    analyze_doc(
        doc_path,
        prompt=args.prompt,
        output=args.output,
        model=args.model,
        base_url=args.base_model_url,
    )
