import sys
from dotenv import load_dotenv

from doc_ai.cli import app, ENV_FILE


def main(argv: list[str] | None = None) -> None:
    load_dotenv(ENV_FILE)
    args = argv if argv is not None else sys.argv[1:]
    app(prog_name="convert.py", args=["convert", *args], standalone_mode=False)


if __name__ == "__main__":
    main()
