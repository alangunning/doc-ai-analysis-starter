import io
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from doc_ai.openai import (
    upload_file,
    input_file_from_url,
    input_file_from_path,
    input_file_from_bytes,
    files,
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
    mock_client.files.create.return_value = SimpleNamespace(id="file-123")

    file_id = upload_file(mock_client, file_path)
    assert file_id == "file-123"
    mock_client.files.create.assert_called_once()

    result = input_file_from_path(mock_client, file_path)
    assert result == {"type": "input_file", "file_id": "file-123"}


def test_upload_file_via_uploads(tmp_path):
    file_path = tmp_path / "big.bin"
    file_path.write_bytes(b"0123456789")
    mock_client = MagicMock()
    mock_client.uploads.create.return_value = SimpleNamespace(id="upl-1")
    mock_client.uploads.parts.create.side_effect = [
        SimpleNamespace(id="part1"),
        SimpleNamespace(id="part2"),
        SimpleNamespace(id="part3"),
    ]
    mock_client.uploads.complete.return_value = SimpleNamespace(
        file=SimpleNamespace(id="file-xyz")
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
    mock_client.uploads.create.return_value = SimpleNamespace(id="upl-1")
    mock_client.uploads.parts.create.side_effect = [
        SimpleNamespace(id="part1"),
        SimpleNamespace(id="part2"),
        SimpleNamespace(id="part3"),
    ]
    mock_client.uploads.complete.return_value = SimpleNamespace(
        file=SimpleNamespace(id="file-xyz")
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


def test_upload_file_keeps_provided_handle_open():
    fh = io.BytesIO(b"data")
    mock_client = MagicMock()
    mock_client.files.create.return_value = SimpleNamespace(id="file-1")

    upload_file(mock_client, fh)

    assert not fh.closed
    mock_client.files.create.assert_called_once()


def test_upload_file_via_uploads_keeps_handle_open():
    fh = io.BytesIO(b"0123456789")
    fh.name = "big.bin"
    mock_client = MagicMock()
    mock_client.uploads.create.return_value = SimpleNamespace(id="upl-1")
    mock_client.uploads.parts.create.side_effect = [
        SimpleNamespace(id="part1"),
        SimpleNamespace(id="part2"),
        SimpleNamespace(id="part3"),
    ]
    mock_client.uploads.complete.return_value = SimpleNamespace(
        file=SimpleNamespace(id="file-xyz")
    )

    upload_file(mock_client, fh, use_upload=True, chunk_size=4)

    assert not fh.closed
    mock_client.uploads.complete.assert_called_once_with(
        "upl-1", part_ids=["part1", "part2", "part3"]
    )


def test_upload_file_env_purpose(monkeypatch, tmp_path):
    file_path = tmp_path / "file.pdf"
    file_path.write_text("content")
    mock_client = MagicMock()
    mock_client.files.create.return_value = SimpleNamespace(id="file-123")

    monkeypatch.setenv("OPENAI_FILE_PURPOSE", "assistants")
    upload_file(mock_client, file_path)

    mock_client.files.create.assert_called_once()
    assert mock_client.files.create.call_args[1]["purpose"] == "assistants"


def test_upload_file_env_force_upload(monkeypatch, tmp_path):
    file_path = tmp_path / "file.bin"
    file_path.write_bytes(b"1234")
    mock_client = MagicMock()
    mock_client.uploads.create.return_value = SimpleNamespace(id="upl-1")
    mock_client.uploads.parts.create.return_value = SimpleNamespace(id="part1")
    mock_client.uploads.complete.return_value = SimpleNamespace(
        file=SimpleNamespace(id="file-x")
    )

    monkeypatch.setenv("OPENAI_USE_UPLOAD", "1")
    monkeypatch.setenv("OPENAI_FILE_PURPOSE", "assistants")
    file_id = upload_file(mock_client, file_path)
    assert file_id == "file-x"
    mock_client.uploads.create.assert_called_once_with(
        purpose="assistants", filename="file.bin", bytes=4, mime_type="application/octet-stream"
    )
    mock_client.files.create.assert_not_called()


def test_open_file_missing_raises(tmp_path):
    missing = tmp_path / "nope.txt"
    with pytest.raises(ValueError, match=f"File not found: {missing}"):
        files._open_file(missing)
