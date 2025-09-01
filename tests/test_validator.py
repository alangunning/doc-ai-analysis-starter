from unittest.mock import MagicMock, patch
from types import SimpleNamespace
import yaml

from doc_ai.converter import OutputFormat
from doc_ai.github.validator import validate_file


def test_validate_file_returns_json(tmp_path):
    raw_path = tmp_path / "raw.pdf"
    rendered_path = tmp_path / "rendered.txt"
    prompt_path = tmp_path / "prompt.yml"

    raw_path.write_bytes(b"raw")
    rendered_path.write_text("text")
    prompt_path.write_text(
        yaml.dump({"model": "validator-model", "messages": [{"role": "user", "content": "Check {format}"}]})
    )

    mock_response = MagicMock()
    mock_response.output = [MagicMock(content=[{"text": "{\"ok\": true}"}])]
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_response

    with patch("doc_ai.github.validator.OpenAI", return_value=mock_client) as mock_openai:
        result = validate_file(raw_path, rendered_path, OutputFormat.TEXT, prompt_path)

    assert result == {"ok": True}
    mock_openai.assert_called_once()
    args, kwargs = mock_client.responses.create.call_args
    assert kwargs["model"] == "validator-model"
    assert isinstance(kwargs["input"], list)


def test_validate_file_fallback_chat_completion(tmp_path):
    raw_path = tmp_path / "raw.pdf"
    rendered_path = tmp_path / "rendered.txt"
    prompt_path = tmp_path / "prompt.yml"

    raw_path.write_bytes(b"raw")
    rendered_path.write_text("text")
    prompt_path.write_text(
        yaml.dump({"model": "validator-model", "messages": [{"role": "user", "content": "Check {format}"}]})
    )

    mock_completion = MagicMock()
    mock_completion.choices = [SimpleNamespace(message=SimpleNamespace(content="{\"ok\": true}"))]
    mock_chat = SimpleNamespace(completions=SimpleNamespace(create=MagicMock(return_value=mock_completion)))
    mock_client = SimpleNamespace(chat=mock_chat)

    with patch("doc_ai.github.validator.OpenAI", return_value=mock_client) as mock_openai:
        result = validate_file(raw_path, rendered_path, OutputFormat.TEXT, prompt_path)

    assert result == {"ok": True}
    mock_openai.assert_called_once()
    mock_chat.completions.create.assert_called_once()
