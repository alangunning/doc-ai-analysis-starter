import argparse
import os
from pathlib import Path

from doc_ai.github import review_pr


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=Path, help="Path to pr-review.prompt.yaml")
    parser.add_argument("pr_body", help="Pull request description")
    parser.add_argument(
        "--model",
        default=os.getenv("PR_REVIEW_MODEL"),
        help="Model name override",
    )
    parser.add_argument(
        "--base-model-url",
        default=os.getenv("PR_REVIEW_BASE_MODEL_URL")
        or os.getenv("BASE_MODEL_URL"),
        help="Model base URL override",
    )
    args = parser.parse_args()
    print(
        review_pr(
            args.pr_body,
            args.prompt,
            model=args.model,
            base_url=args.base_model_url,
        )
    )
