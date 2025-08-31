import argparse
from pathlib import Path

from doc_ai.github import build_vector_store


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Directory containing Markdown files")
    args = parser.parse_args()
    build_vector_store(args.source)
