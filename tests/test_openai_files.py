import types
from pathlib import Path
from unittest.mock import MagicMock

from doc_ai.openai import (
    upload_file,
    input_file_from_url,
    input_file_from_path,
    input_file_from_bytes,
)


def test_input_file_from_url():
    url = "https://example.com/foo.pdf"
    assert input_file_from_url(url) == {"type": "input_file", "file_url": url}


def test_input_file_from_bytes():
    data = b"hello"
    result = input_file_from_bytes("test.txt", data)
    assert result["type"] == "input_file"
    assert result["filename"] == "test.txt"
    assert result["file_data"].startswith("data:text/plain;base64,")


def test_upload_and_input_from_path(tmp_path):
    file_path = tmp_path / "file.pdf"
    file_path.write_text("content")
    mock_client = MagicMock()
    mock_client.files.create.return_value = types.SimpleNamespace(id="file-123")

    file_id = upload_file(mock_client, file_path)
    assert file_id == "file-123"
    mock_client.files.create.assert_called_once()

    result = input_file_from_path(mock_client, file_path)
    assert result == {"type": "input_file", "file_id": "file-123"}
