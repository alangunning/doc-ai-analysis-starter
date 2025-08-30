import argparse
import subprocess


def merge(pr_number: int) -> None:
    subprocess.run(["gh", "pr", "merge", str(pr_number), "--merge"], check=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("pr_number", type=int)
    args = p.parse_args()
    merge(args.pr_number)
