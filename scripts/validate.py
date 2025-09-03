import argparse
import os
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

from doc_ai import OutputFormat, suffix_for_format
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
        ".dogtags": OutputFormat.DOCTAGS,
    }
    try:
        return mapping[path.suffix.lower()]
    except KeyError as exc:
        valid = ", ".join(mapping.keys())
        raise SystemExit(
            f"Unknown file extension '{path.suffix}'. Expected one of: {valid}"
        ) from exc


if __name__ == "__main__":
    load_dotenv()
    from doc_ai.github import validate_file
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("rendered", type=Path, nargs="?")
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        help="Format of converted file (inferred from --rendered if omitted)",
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        help="Prompt file (overrides auto-detected *.validate.prompt.yaml)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("VALIDATE_MODEL"),
        help="Model name override",
    )
    parser.add_argument(
        "--base-model-url",
        default=os.getenv("VALIDATE_BASE_MODEL_URL")
        or os.getenv("BASE_MODEL_URL")
        or "https://api.openai.com/v1",
        help="Model base URL override",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write request/response details to this file",
    )
    if len(sys.argv) > 1 and sys.argv[1] in {"help", "-h", "--help"}:
        parser.print_help()
        raise SystemExit(0)
    args = parser.parse_args()

    console = Console()
    logger = None
    log_path = args.log_file
    if args.verbose or log_path is not None:
        logger = logging.getLogger("doc_ai.validate")
        logger.setLevel(logging.DEBUG)
        if args.verbose:
            sh = RichHandler(console=console, show_time=False)
            sh.setLevel(logging.DEBUG)
            logger.addHandler(sh)
        if log_path is None:
            log_path = args.raw.with_suffix(".validate.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)

    meta = load_metadata(args.raw)
    file_hash = compute_hash(args.raw)
    if meta.blake2b == file_hash and is_step_done(meta, "validation"):
        raise SystemExit(0)
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}

    if args.rendered is None:
        fmt = OutputFormat(args.format) if args.format else OutputFormat.MARKDOWN
        rendered = args.raw.with_name(
            args.raw.name + f".converted{suffix_for_format(fmt)}"
        )
    else:
        rendered = args.rendered
        fmt = OutputFormat(args.format) if args.format else infer_format(rendered)

    prompt_path = args.prompt
    if prompt_path is None:
        doc_prompt = args.raw.with_name(f"{args.raw.stem}.validate.prompt.yaml")
        dir_prompt = args.raw.with_name("validate.prompt.yaml")
        if doc_prompt.exists():
            prompt_path = doc_prompt
        elif dir_prompt.exists():
            prompt_path = dir_prompt
        else:
            prompt_path = Path(
                ".github/prompts/validate-output.validate.prompt.yaml"
            )
    verdict = validate_file(
        args.raw,
        rendered,
        fmt,
        prompt_path,
        model=args.model,
        base_url=args.base_model_url,
        show_progress=True,
        logger=logger,
        console=console,
    )
    now = datetime.now(timezone.utc).isoformat()
    meta.date_modified = now
    mark_step(
        meta,
        "validation",
        done=verdict.get("match", False),
        outputs=[rendered.name],
        inputs={
            "model": args.model,
            "document": str(args.raw),
            "rendered": rendered.name,
            "rendered_blake2b": compute_hash(rendered),
            "prompt": prompt_path.name,
            "base_url": args.base_model_url,
            "format": fmt.value,
            "validated_at": now,
            "verdict": verdict,
        },
    )
    save_metadata(args.raw, meta)
    if not verdict.get("match", False):
        raise SystemExit(f"Mismatch detected: {verdict}")
