import types
import tempfile
from pathlib import Path
import sys
import yaml
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from doc_ai.openai.responses import create_response
from doc_ai.github.prompts import run_prompt


class StubResponses:
    def create(self, **kwargs):
        assert "model" in kwargs and "input" in kwargs
        return types.SimpleNamespace(output_text="ok")


class StubClient:
    def __init__(self):
        self.responses = StubResponses()


def validate_create_response() -> None:
    client = StubClient()
    create_response(client, model="gpt-4o-mini", texts="hi")


def validate_run_prompt() -> None:
    client = StubClient()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "prompt.yml"
        path.write_text(
            yaml.dump({"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hi"}]})
        )
        with patch("doc_ai.github.prompts.OpenAI", return_value=client):
            run_prompt(path, "input")


def main() -> None:
    validate_create_response()
    validate_run_prompt()
    print("all openai call sites validated")


if __name__ == "__main__":
    main()
