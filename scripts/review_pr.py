import argparse
from pathlib import Path

from docai.github import review_pr


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=Path, help="Path to pr-review.prompt.yaml")
    parser.add_argument("pr_body", help="Pull request description")
    args = parser.parse_args()
    print(review_pr(args.pr_body, args.prompt))
