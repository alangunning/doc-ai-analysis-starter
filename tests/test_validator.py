from unittest.mock import MagicMock, patch
import yaml

from doc_ai.converter import OutputFormat
from doc_ai.github.validator import validate_file
from doc_ai.cli import validate_doc
from doc_ai.metadata import load_metadata, metadata_path


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
    mock_response.choices = [
        MagicMock(message=MagicMock(content="{\"ok\": true}"))
    ]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("doc_ai.github.validator.OpenAI", return_value=mock_client) as mock_openai:
        result = validate_file(raw_path, rendered_path, OutputFormat.TEXT, prompt_path)

    assert result == {"ok": True}
    mock_openai.assert_called_once()
    args, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["model"] == "validator-model"
    assert isinstance(kwargs["messages"], list)
    user_msg = kwargs["messages"][0]
    file_part = user_msg["content"][1]
    assert file_part["type"] == "file"
    assert file_part["file"]["filename"] == "raw.pdf"


def test_validate_doc_updates_metadata(tmp_path):
    raw = tmp_path / "raw.pdf"
    rendered = tmp_path / "raw.pdf.converted.md"
    prompt = tmp_path / "prompt.yml"
    raw.write_bytes(b"pdf")
    rendered.write_text("md")
    prompt.write_text(yaml.dump({"model": "validator", "messages": []}))
    with patch("doc_ai.cli.validate_file", return_value={"match": True}):
        validate_doc(raw, rendered, OutputFormat.MARKDOWN, prompt)
    assert not metadata_path(rendered).exists()
    meta = load_metadata(raw)
    assert meta.extra["steps"]["validation"] is True
    assert meta.extra["outputs"]["validation"] == [rendered.name]
    inputs = meta.extra["inputs"]["validation"]
    assert inputs["prompt"] == prompt.name
    assert inputs["rendered"] == rendered.name
    assert inputs["format"] == OutputFormat.MARKDOWN.value
