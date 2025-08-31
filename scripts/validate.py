import argparse
import os
from pathlib import Path

from doc_ai import OutputFormat
from doc_ai.github import validate_file
from doc_ai.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)


def infer_format(path: Path) -> OutputFormat:
    mapping = {
        ".md": OutputFormat.MARKDOWN,
        ".html": OutputFormat.HTML,
        ".json": OutputFormat.JSON,
        ".txt": OutputFormat.TEXT,
        ".doctags": OutputFormat.DOCTAGS,
    }
    try:
        return mapping[path.suffix]
    except KeyError as exc:
        valid = ", ".join(mapping.keys())
        raise SystemExit(f"Unknown file extension '{path.suffix}'. Expected one of: {valid}") from exc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("rendered", type=Path)
    parser.add_argument("--format", choices=[f.value for f in OutputFormat])
    parser.add_argument(
        "--prompt",
        type=Path,
        default=Path(".github/workflows/validate-output.prompt.yaml"),
    )
    parser.add_argument(
        "--model",
        default=os.getenv("VALIDATE_MODEL"),
        help="Model name override",
    )
    parser.add_argument(
        "--base-model-url",
        default=os.getenv("VALIDATE_BASE_MODEL_URL")
        or os.getenv("BASE_MODEL_URL"),
        help="Model base URL override",
    )
    args = parser.parse_args()

    meta = load_metadata(args.raw)
    file_hash = compute_hash(args.raw)
    if meta.blake2b == file_hash and is_step_done(meta, "validation"):
        raise SystemExit(0)
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}
    fmt = OutputFormat(args.format) if args.format else infer_format(args.rendered)
    verdict = validate_file(
        args.raw,
        args.rendered,
        fmt,
        args.prompt,
        model=args.model,
        base_url=args.base_model_url,
    )
    if not verdict.get("match", False):
        raise SystemExit(f"Mismatch detected: {verdict}")
    mark_step(meta, "validation")
    save_metadata(args.raw, meta)
