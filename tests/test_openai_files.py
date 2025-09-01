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


def test_upload_file_via_uploads(tmp_path):
    file_path = tmp_path / "big.bin"
    file_path.write_bytes(b"0123456789")
    mock_client = MagicMock()
    mock_client.uploads.create.return_value = types.SimpleNamespace(id="upl-1")
    mock_client.uploads.parts.create.side_effect = [
        types.SimpleNamespace(id="part1"),
        types.SimpleNamespace(id="part2"),
        types.SimpleNamespace(id="part3"),
    ]
    mock_client.uploads.complete.return_value = types.SimpleNamespace(
        file=types.SimpleNamespace(id="file-xyz")
    )

    file_id = upload_file(mock_client, file_path, use_upload=True, chunk_size=4)
    assert file_id == "file-xyz"

    mock_client.uploads.create.assert_called_once_with(
        purpose="user_data", filename="big.bin", bytes=10, mime_type="application/octet-stream"
    )
    assert mock_client.uploads.parts.create.call_count == 3
    mock_client.uploads.complete.assert_called_once_with(
        "upl-1", part_ids=["part1", "part2", "part3"]
    )


def test_upload_large_file_reports_progress(tmp_path):
    file_path = tmp_path / "big.bin"
    file_path.write_bytes(b"0123456789")
    mock_client = MagicMock()
    mock_client.uploads.create.return_value = types.SimpleNamespace(id="upl-1")
    mock_client.uploads.parts.create.side_effect = [
        types.SimpleNamespace(id="part1"),
        types.SimpleNamespace(id="part2"),
        types.SimpleNamespace(id="part3"),
    ]
    mock_client.uploads.complete.return_value = types.SimpleNamespace(
        file=types.SimpleNamespace(id="file-xyz")
    )

    seen: list[int] = []

    upload_file(
        mock_client,
        file_path,
        use_upload=True,
        chunk_size=4,
        progress=lambda n: seen.append(n),
    )

    assert seen == [4, 4, 2]
