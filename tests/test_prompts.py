from pathlib import Path
from unittest.mock import MagicMock, patch
import yaml

from doc_ai.github.prompts import run_prompt


def test_run_prompt_uses_spec_and_input(tmp_path):
    prompt_file = tmp_path / "prompt.yml"
    prompt_file.write_text(
        yaml.dump({"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]})
    )

    mock_response = MagicMock()
    mock_response.output = [MagicMock(content=[{"text": "result"}])]
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_response

    with patch("doc_ai.github.prompts.OpenAI", return_value=mock_client) as mock_openai:
        output = run_prompt(prompt_file, "input")

    assert output == "result"
    mock_openai.assert_called_once()
    args, kwargs = mock_client.responses.create.call_args
    assert kwargs["model"] == "test-model"
    messages = kwargs["input"]
    assert messages[0]["content"] == "Hello\n\ninput"
