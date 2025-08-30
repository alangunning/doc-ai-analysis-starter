"""CLI helper to merge pull requests via the GitHub CLI."""

import argparse
import subprocess

from dotenv import load_dotenv

load_dotenv()


def merge_pr(pr_number: int) -> None:
    """Merge pull request ``pr_number`` using the GitHub CLI."""

    subprocess.run(["gh", "pr", "merge", str(pr_number), "--merge"], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_number", type=int)
    args = parser.parse_args()
    merge_pr(args.pr_number)

