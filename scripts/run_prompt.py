import argparse
from pathlib import Path

from docai.github import run_prompt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=Path)
    parser.add_argument("markdown_doc", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file; defaults to <doc>.<prompt>.json next to the source",
    )
    args = parser.parse_args()

    result = run_prompt(args.prompt, args.markdown_doc.read_text())
    prompt_name = args.prompt.name.replace(".prompt.yaml", "")
    out_path = (
        args.output
        if args.output
        else args.markdown_doc.with_suffix(f".{prompt_name}.json")
    )
    out_path.write_text(result + "\n", encoding="utf-8")
