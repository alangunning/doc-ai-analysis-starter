import argparse
from pathlib import Path

from docai import OutputFormat
from docai.github import validate_file


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
        default=Path("prompts/validate-output.prompt.yaml"),
    )
    args = parser.parse_args()

    fmt = OutputFormat(args.format) if args.format else infer_format(args.rendered)
    verdict = validate_file(args.raw, args.rendered, fmt, args.prompt)
    if not verdict.get("match", False):
        raise SystemExit(f"Mismatch detected: {verdict}")
