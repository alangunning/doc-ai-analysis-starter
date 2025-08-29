import argparse
import os
import subprocess


def is_authorized(user: str, repo: str) -> bool:
    cmd = ["gh", "api", f"repos/{repo}/collaborators/{user}"]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def merge_pr(pr_number: str, user: str, repo: str) -> None:
    if not is_authorized(user, repo):
        raise SystemExit(f"{user} is not authorized to merge")
    subprocess.run(["gh", "pr", "merge", pr_number, "--merge"], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pr", help="Pull request number to merge")
    parser.add_argument("--user", default=os.environ.get("COMMENT_AUTHOR"))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    args = parser.parse_args()

    if not args.user or not args.repo:
        raise SystemExit("user and repo must be provided")

    merge_pr(args.pr, args.user, args.repo)

