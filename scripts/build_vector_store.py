import sys

from dotenv import load_dotenv

from doc_ai.cli import ENV_FILE, app


def main(argv: list[str] | None = None) -> None:
    load_dotenv(ENV_FILE)
    args = argv if argv is not None else sys.argv[1:]
    app(prog_name="build_vector_store.py", args=["embed", *args], standalone_mode=False)


if __name__ == "__main__":
    main()
