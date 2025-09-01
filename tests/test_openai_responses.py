from unittest.mock import MagicMock

from pathlib import Path
from unittest.mock import MagicMock

from doc_ai.openai import (
    create_response,
    create_response_with_file_url,
    input_file_from_bytes,
)


def test_create_response_with_mixed_inputs():
    client = MagicMock()
    create_response(
        client,
        model="gpt-4.1",
        texts=["what is in this file?"],
        file_urls=["https://example.com/file.pdf"],
        file_ids=["file-123"],
        file_bytes=[("demo.txt", b"hello")],
    )

    expected_content = [
        {"type": "input_text", "text": "what is in this file?"},
        {"type": "input_file", "file_url": "https://example.com/file.pdf"},
        {"type": "input_file", "file_id": "file-123"},
        input_file_from_bytes("demo.txt", b"hello"),
    ]

    client.responses.create.assert_called_once_with(
        model="gpt-4.1",
        input=[{"role": "user", "content": expected_content}],
    )


def test_create_response_with_file_url_wrapper():
    client = MagicMock()
    create_response_with_file_url(
        client,
        model="gpt-4.1",
        file_url="https://example.com/file.pdf",
        prompt="what is in this file?",
    )
    client.responses.create.assert_called_once_with(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "what is in this file?"},
                    {"type": "input_file", "file_url": "https://example.com/file.pdf"},
                ],
            }
        ],
    )


def test_create_response_with_file_paths(monkeypatch, tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("hi")

    calls = []

    def fake_upload_file(client, path, purpose, *, use_upload):
        calls.append(use_upload)
        return "file-id"

    monkeypatch.setattr("doc_ai.openai.responses.upload_file", fake_upload_file)
    monkeypatch.setattr("doc_ai.openai.responses.DEFAULT_CHUNK_SIZE", 1)

    client = MagicMock()
    create_response(client, model="gpt-4.1", file_paths=[file_path])

    assert calls == [True]
    client.responses.create.assert_called_once()


def test_create_response_with_system_message():
    client = MagicMock()
    create_response(
        client,
        model="gpt-4.1",
        system="sys",
        texts=["hello"],
    )

    client.responses.create.assert_called_once_with(
        model="gpt-4.1",
        input=[
            {"role": "system", "content": "sys"},
            {"role": "user", "content": [{"type": "input_text", "text": "hello"}]},
        ],
    )

