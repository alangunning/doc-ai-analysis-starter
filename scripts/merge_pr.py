"""CLI helper to merge pull requests via the GitHub CLI."""

import argparse

from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()
    from doc_ai.github.pr import merge_pr
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_number", type=int)
    args = parser.parse_args()
    merge_pr(args.pr_number)
