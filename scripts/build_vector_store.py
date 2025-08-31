import argparse
from pathlib import Path

from doc_ai.github import build_vector_store


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Directory containing Markdown files")
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Abort immediately on the first HTTP error",
    )
    args = parser.parse_args()
    build_vector_store(args.source, fail_fast=args.fail_fast)
