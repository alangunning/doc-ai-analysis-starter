from unittest.mock import MagicMock, patch

import pytest
import yaml

from doc_ai.github.prompts import run_prompt


def test_run_prompt_uses_spec_and_input(tmp_path, monkeypatch):
    prompt_file = tmp_path / "prompt.yml"
    prompt_file.write_text(
        yaml.dump(
            {"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]}
        )
    )

    monkeypatch.setenv("GITHUB_TOKEN", "token")

    mock_response = MagicMock(output_text="result")
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_response

    with patch("doc_ai.github.prompts.OpenAI", return_value=mock_client) as mock_openai:
        output, _ = run_prompt(prompt_file, "input")

    assert output == "result"
    mock_openai.assert_called_once()
    args, kwargs = mock_client.responses.create.call_args
    assert kwargs["model"] == "test-model"
    messages = kwargs["input"]
    assert messages[0]["content"][0]["text"] == "Hello\n\ninput"


def test_run_prompt_uses_env_base_and_token(monkeypatch, tmp_path):
    prompt_file = tmp_path / "prompt.yml"
    prompt_file.write_text(yaml.dump({"model": "test-model", "messages": []}))

    monkeypatch.setenv("GITHUB_TOKEN", "gh-test")
    monkeypatch.setenv("BASE_MODEL_URL", "https://example.com")

    mock_response = MagicMock(output_text="result")
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_response

    with patch("doc_ai.github.prompts.OpenAI", return_value=mock_client) as mock_openai:
        run_prompt(prompt_file, "input")

    args, kwargs = mock_openai.call_args
    assert kwargs["api_key"] == "gh-test"
    assert kwargs["base_url"] == "https://example.com"


def test_run_prompt_requires_token(monkeypatch, tmp_path):
    prompt_file = tmp_path / "p.yml"
    prompt_file.write_text(yaml.dump({"model": "m", "messages": []}))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with patch("doc_ai.github.prompts.OpenAI") as mock_openai:
        with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
            run_prompt(prompt_file, "input")
    mock_openai.assert_not_called()


def test_run_prompt_uses_openai_token_for_openai_base(monkeypatch, tmp_path):
    prompt_file = tmp_path / "prompt.yml"
    prompt_file.write_text(yaml.dump({"model": "m", "messages": []}))
    monkeypatch.setenv("OPENAI_API_KEY", "oa-test")
    monkeypatch.setenv("BASE_MODEL_URL", "https://api.openai.com/v1")

    mock_response = MagicMock(output_text="result")
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_response

    with patch("doc_ai.github.prompts.OpenAI", return_value=mock_client) as mock_openai:
        run_prompt(prompt_file, "input")

    args, kwargs = mock_openai.call_args
    assert kwargs["api_key"] == "oa-test"
    assert kwargs["base_url"] == "https://api.openai.com/v1"


def test_run_prompt_requires_openai_token(monkeypatch, tmp_path):
    prompt_file = tmp_path / "prompt.yml"
    prompt_file.write_text(yaml.dump({"model": "m", "messages": []}))
    monkeypatch.setenv("BASE_MODEL_URL", "https://api.openai.com/v1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with patch("doc_ai.github.prompts.OpenAI") as mock_openai:
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            run_prompt(prompt_file, "input")
    mock_openai.assert_not_called()


def test_run_prompt_requires_model_and_messages(tmp_path, monkeypatch):
    prompt_file = tmp_path / "prompt.yml"
    prompt_file.write_text(yaml.dump({}))
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    with pytest.raises(ValueError, match="model.*messages"):
        run_prompt(prompt_file, "input")


def test_run_prompt_validates_message_fields(tmp_path, monkeypatch):
    prompt_file = tmp_path / "prompt.yml"
    prompt_file.write_text(yaml.dump({"model": "m", "messages": [{}]}))
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    with pytest.raises(ValueError, match="role.*content"):
        run_prompt(prompt_file, "input")
