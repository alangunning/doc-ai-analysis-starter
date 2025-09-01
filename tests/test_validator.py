from unittest.mock import MagicMock, patch
import runpy
import sys
from pathlib import Path
import yaml
from unittest.mock import MagicMock, patch

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
        yaml.dump(
            {
                "name": "Validate Rendered Output",
                "description": "Compare original documents with their rendered representation.",
                "model": "validator-model",
                "modelParameters": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": "System instructions"},
                    {"role": "user", "content": "Check {format}"},
                ],
            }
        )
    )

    mock_response = MagicMock(output_text="{\"ok\": true}")
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_response

    uploads = []

    def fake_upload_file(client, path, purpose, *, use_upload, progress=None):
        uploads.append((Path(path).name, purpose, use_upload))
        return f"{Path(path).name}-id"

    with patch(
        "doc_ai.github.validator.OpenAI", return_value=mock_client
    ) as mock_openai, patch(
        "doc_ai.openai.responses.upload_file", side_effect=fake_upload_file
    ):
        result = validate_file(raw_path, rendered_path, OutputFormat.TEXT, prompt_path)

    assert result == {"ok": True}
    mock_openai.assert_called_once()
    assert uploads == [
        ("raw.pdf", "assistants", False),
        ("rendered.txt", "assistants", False),
    ]
    args, kwargs = mock_client.responses.create.call_args
    assert kwargs["model"] == "validator-model"
    user_msg = kwargs["input"][1]
    content = user_msg["content"]
    assert content[0] == {"type": "input_text", "text": "Check text"}
    file_ids = [part["file_id"] for part in content if part["type"] == "input_file"]
    assert file_ids == ["raw.pdf-id", "rendered.txt-id"]


def test_validate_file_large_uses_uploads(monkeypatch, tmp_path):
    raw_path = tmp_path / "raw.pdf"
    rendered_path = tmp_path / "rendered.txt"
    prompt_path = tmp_path / "prompt.yml"

    raw_path.write_bytes(b"raw")
    rendered_path.write_text("text")
    prompt_path.write_text(
        yaml.dump(
            {
                "name": "Validate Rendered Output",
                "description": "Compare original documents with their rendered representation.",
                "model": "validator-model",
                "modelParameters": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": "System instructions"},
                    {"role": "user", "content": "Check {format}"},
                ],
            }
        )
    )

    called: list[bool] = []

    def fake_upload_file(client, path, purpose, *, use_upload, progress=None):
        called.append(use_upload)
        return f"{Path(path).name}-id"

    monkeypatch.setattr("doc_ai.openai.responses.upload_file", fake_upload_file)
    monkeypatch.setattr("doc_ai.openai.responses.DEFAULT_CHUNK_SIZE", 1)

    mock_response = MagicMock(output_text="{}")
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_response

    with patch("doc_ai.github.validator.OpenAI", return_value=mock_client):
        validate_file(raw_path, rendered_path, OutputFormat.TEXT, prompt_path)

    assert called == [True, True]


def test_validate_file_with_urls(tmp_path):
    raw_url = "https://example.com/raw.pdf"
    rendered_url = "https://example.com/rendered.txt"
    prompt_path = tmp_path / "prompt.yml"

    prompt_path.write_text(
        yaml.dump(
            {
                "name": "Validate Rendered Output",
                "description": "Compare original documents with their rendered representation.",
                "model": "validator-model",
                "modelParameters": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": "System instructions"},
                    {"role": "user", "content": "Check {format}"},
                ],
            }
        )
    )

    mock_response = MagicMock(output_text="{}")
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_response

    with patch("doc_ai.github.validator.OpenAI", return_value=mock_client), \
         patch("doc_ai.openai.responses.upload_file") as up:
        validate_file(raw_url, rendered_url, OutputFormat.TEXT, prompt_path)

    up.assert_not_called()
    args, kwargs = mock_client.responses.create.call_args
    content = kwargs["input"][1]["content"]
    file_urls = [part["file_url"] for part in content if part["type"] == "input_file"]
    assert file_urls == [raw_url, rendered_url]


def test_validate_file_forces_openai_base(monkeypatch, tmp_path):
    raw_path = tmp_path / "raw.pdf"
    rendered_path = tmp_path / "rendered.txt"
    prompt_path = tmp_path / "prompt.yml"

    raw_path.write_bytes(b"raw")
    rendered_path.write_text("text")
    prompt_path.write_text(
        yaml.dump(
            {
                "name": "Validate Rendered Output",
                "description": "Compare original documents with their rendered representation.",
                "model": "validator-model",
                "modelParameters": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": "System instructions"},
                    {"role": "user", "content": "Check {format}"},
                ],
            }
        )
    )

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_response = MagicMock(output_text="{}")
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_response

    with patch(
        "doc_ai.github.validator.OpenAI", return_value=mock_client
    ) as mock_openai, patch(
        "doc_ai.openai.responses.upload_file", return_value="file1"
    ):
        validate_file(
            raw_path,
            rendered_path,
            OutputFormat.TEXT,
            prompt_path,
            base_url="https://models.github.ai/inference",
        )

    args, kwargs = mock_openai.call_args
    assert kwargs["base_url"] == "https://api.openai.com/v1"
    assert kwargs["api_key"] == "sk-test"


def test_validate_file_custom_base_uses_github_token(monkeypatch, tmp_path):
    raw_path = tmp_path / "raw.pdf"
    rendered_path = tmp_path / "rendered.txt"
    prompt_path = tmp_path / "prompt.yml"

    raw_path.write_bytes(b"raw")
    rendered_path.write_text("text")
    prompt_path.write_text(
        yaml.dump(
            {
                "name": "Validate Rendered Output",
                "description": "Compare original documents with their rendered representation.",
                "model": "validator-model",
                "modelParameters": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": "System instructions"},
                    {"role": "user", "content": "Check {format}"},
                ],
            }
        )
    )

    monkeypatch.setenv("GITHUB_TOKEN", "gh-test")
    mock_response = MagicMock(output_text="{}")
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_response

    with patch(
        "doc_ai.github.validator.OpenAI", return_value=mock_client
    ) as mock_openai, patch(
        "doc_ai.openai.responses.upload_file", return_value="file1"
    ):
        validate_file(
            raw_path,
            rendered_path,
            OutputFormat.TEXT,
            prompt_path,
            base_url="https://custom.provider/v1",
        )

    args, kwargs = mock_openai.call_args
    assert kwargs["base_url"] == "https://custom.provider/v1"
    assert kwargs["api_key"] == "gh-test"


def test_validate_doc_updates_metadata(tmp_path):
    raw = tmp_path / "raw.pdf"
    rendered = tmp_path / "raw.pdf.converted.md"
    prompt = tmp_path / "prompt.yml"
    raw.write_bytes(b"pdf")
    rendered.write_text("md")
    prompt.write_text(
        yaml.dump(
            {
                "name": "Validate Rendered Output",
                "description": "Compare original documents with their rendered representation.",
                "model": "validator",
                "modelParameters": {"temperature": 0},
                "messages": [],
            }
        )
    )
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


def test_validate_script_uses_env_defaults(monkeypatch, tmp_path):
    raw = tmp_path / "raw.pdf"
    rendered = tmp_path / "rendered.md"
    prompt = tmp_path / "prompt.yml"
    raw.write_bytes(b"pdf")
    rendered.write_text("md")
    prompt.write_text(
        yaml.dump(
            {
                "name": "Validate Rendered Output",
                "description": "Compare original documents with their rendered representation.",
                "model": "validator",
                "modelParameters": {"temperature": 0},
                "messages": [],
            }
        )
    )

    monkeypatch.setenv("VALIDATE_MODEL", "env-model")
    monkeypatch.setenv("VALIDATE_BASE_MODEL_URL", "https://test.base")

    called: dict[str, str] = {}

    def fake_validate_file(raw_path, rendered_path, fmt, prompt_path, model=None, base_url=None):
        called["model"] = model
        called["base_url"] = base_url
        return {"match": True}

    monkeypatch.setattr("doc_ai.github.validate_file", fake_validate_file)
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "validate.py"
    monkeypatch.setattr(sys, "argv", [
        str(script_path),
        str(raw),
        str(rendered),
        "--prompt",
        str(prompt),
    ])

    runpy.run_path(str(script_path), run_name="__main__")

    assert called["model"] == "env-model"
    assert called["base_url"] == "https://test.base"


def test_validate_script_cli_overrides_env(monkeypatch, tmp_path):
    raw = tmp_path / "raw.pdf"
    rendered = tmp_path / "rendered.md"
    prompt = tmp_path / "prompt.yml"
    raw.write_bytes(b"pdf")
    rendered.write_text("md")
    prompt.write_text(
        yaml.dump(
            {
                "name": "Validate Rendered Output",
                "description": "Compare original documents with their rendered representation.",
                "model": "validator",
                "modelParameters": {"temperature": 0},
                "messages": [],
            }
        )
    )

    monkeypatch.setenv("VALIDATE_MODEL", "env-model")
    monkeypatch.setenv("VALIDATE_BASE_MODEL_URL", "https://env.base")

    called: dict[str, str] = {}

    def fake_validate_file(raw_path, rendered_path, fmt, prompt_path, model=None, base_url=None):
        called["model"] = model
        called["base_url"] = base_url
        return {"match": True}

    monkeypatch.setattr("doc_ai.github.validate_file", fake_validate_file)
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "validate.py"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(script_path),
            str(raw),
            str(rendered),
            "--prompt",
            str(prompt),
            "--model",
            "cli-model",
            "--base-model-url",
            "https://cli.base",
        ],
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert called["model"] == "cli-model"
    assert called["base_url"] == "https://cli.base"
