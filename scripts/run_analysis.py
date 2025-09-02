import argparse
import os
from pathlib import Path

from doc_ai.cli import analyze_doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown_doc", type=Path)
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

    analyze_doc(
        args.markdown_doc,
        prompt=args.prompt,
        output=args.output,
        model=args.model,
        base_url=args.base_model_url,
    )
