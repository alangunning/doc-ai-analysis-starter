from unittest.mock import MagicMock

import pytest
from openai import OpenAIError

import doc_ai.openai.responses as responses_module

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
        {
            "type": "input_text",
            "text": "what is in this file?",
        },
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
                    {
                        "type": "input_text",
                        "text": "what is in this file?",
                    },
                    {"type": "input_file", "file_url": "https://example.com/file.pdf"},
                ],
            }
        ],
    )


def test_create_response_with_file_paths(monkeypatch, tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("hi")

    calls = []

    def fake_upload_file(
        client, path, purpose, *, use_upload=None, progress=None, logger=None
    ):
        calls.append(use_upload)
        return "file-id"

    monkeypatch.setattr("doc_ai.openai.responses.upload_file", fake_upload_file)

    client = MagicMock()
    create_response(client, model="gpt-4.1", file_paths=[file_path])

    assert calls == [None]
    client.responses.create.assert_called_once()


def test_create_response_with_single_path(monkeypatch, tmp_path):
    file_path = tmp_path / "single.txt"
    file_path.write_text("hi")

    uploads: list = []

    def fake_upload_file(
        client, path, purpose, *, use_upload=None, progress=None, logger=None
    ):
        uploads.append(path)
        return "file-id"

    monkeypatch.setattr("doc_ai.openai.responses.upload_file", fake_upload_file)

    client = MagicMock()
    create_response(client, model="gpt-4.1", file_paths=file_path)

    assert uploads == [file_path]
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
            {"role": "system", "content": [{"type": "input_text", "text": "sys"}]},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "hello",
                    }
                ],
            },
        ],
    )

def test_create_response_respects_file_purpose_env(monkeypatch, tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("hi")

    calls = []

    def fake_upload_file(
        client, path, purpose, *, use_upload=None, progress=None, logger=None
    ):
        calls.append(purpose)
        return "file-id"

    monkeypatch.setattr("doc_ai.openai.responses.upload_file", fake_upload_file)
    monkeypatch.setenv("OPENAI_FILE_PURPOSE", "assistants")

    client = MagicMock()
    create_response(client, model="gpt-4.1", file_paths=[file_path])

    assert calls == ["assistants"]
    client.responses.create.assert_called_once()


def test_create_response_passes_text_format():
    client = MagicMock()
    create_response(
        client,
        model="gpt-4.1",
        texts=["hi"],
        text={"format": {"type": "json_schema"}},
    )
    client.responses.create.assert_called_once_with(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "hi",
                    }
                ],
            }
        ],
        text={"format": {"type": "json_schema"}},
    )


def test_create_response_retries_exhausted(monkeypatch):
    client = MagicMock()
    client.responses.create.side_effect = OpenAIError("boom")
    monkeypatch.setattr(responses_module.time, "sleep", lambda _s: None)

    with pytest.raises(RuntimeError, match="Responses API request failed after 2 attempts"):
        create_response(client, model="gpt-4.1", retries=2)

    assert client.responses.create.call_count == 2


def test_create_response_passes_timeout():
    client = MagicMock()
    create_response(client, model="gpt-4.1", texts=["hi"], request_timeout=10)
    client.responses.create.assert_called_once_with(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "hi"},
                ],
            }
        ],
        timeout=10,
    )

