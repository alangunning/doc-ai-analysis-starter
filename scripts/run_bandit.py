import subprocess


def main() -> int:
    """Run Bandit security checks on source files."""
    cmd = ["bandit", "-q", "-r", "doc_ai", "scripts"]
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
