import argparse
import os
from pathlib import Path

from doc_ai.github import run_prompt
from doc_ai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=Path)
    parser.add_argument("markdown_doc", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file; defaults to <doc>.<prompt>.json next to the source",
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

    prompt_name = args.prompt.name.replace(".prompt.yaml", "")
    step_name = "analysis"

    meta = load_metadata(args.markdown_doc)
    file_hash = compute_hash(args.markdown_doc)
    if meta.blake2b == file_hash and is_step_done(meta, step_name):
        raise SystemExit(0)
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}

    result = run_prompt(
        args.prompt,
        args.markdown_doc.read_text(),
        model=args.model,
        base_url=args.base_model_url,
    )
    out_path = (
        args.output
        if args.output
        else args.markdown_doc.with_suffix(f".{prompt_name}.json")
    )
    out_path.write_text(result + "\n", encoding="utf-8")
    mark_step(meta, step_name)
    save_metadata(args.markdown_doc, meta)
