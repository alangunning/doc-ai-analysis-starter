"""CLI helper to merge pull requests via the GitHub CLI."""

import argparse

from docai.pr import merge_pr


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_number", type=int)
    args = parser.parse_args()
    merge_pr(args.pr_number)
