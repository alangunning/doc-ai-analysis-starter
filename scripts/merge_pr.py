"""CLI helper to merge pull requests via the GitHub CLI."""

import argparse

from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    from doc_ai.github.pr import merge_pr

    parser = argparse.ArgumentParser()
    parser.add_argument("pr_number", type=int)
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show merge command without executing"
    )
    args = parser.parse_args()
    merge_pr(args.pr_number, yes=args.yes, dry_run=args.dry_run)
