import argparse
import os
from pathlib import Path

from ai_doc_analysis_starter.github import review_pr


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=Path, help="Path to pr-review.prompt.yaml")
    parser.add_argument("pr_body", help="Pull request description")
    parser.add_argument(
        "--model",
        default=os.getenv("PR_REVIEW_MODEL"),
        help="Model name override",
    )
    args = parser.parse_args()
    print(review_pr(args.pr_body, args.prompt, model=args.model))
