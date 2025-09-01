from unittest.mock import MagicMock, patch
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
        result = validate_file(
            raw_path,
            rendered_path,
            OutputFormat.TEXT,
            prompt_path,
            request_metadata={"raw": raw_path.name, "rendered": rendered_path.name},
        )

    assert result == {"ok": True}
    mock_openai.assert_called_once()
    args, kwargs = mock_client.responses.create.call_args
    assert kwargs["model"] == "validator-model"
    assert isinstance(kwargs["input"], list)
    assert kwargs["metadata"] == {"raw": "raw.pdf", "rendered": "rendered.txt"}
