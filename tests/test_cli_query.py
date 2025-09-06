import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from typer.testing import CliRunner

import doc_ai.cli.query as query_module


def _setup_store(tmp_path):
    doc1 = tmp_path / "doc1.md"
    doc1.write_text("alpha")
    (tmp_path / "doc1.md.embedding.json").write_text(
        json.dumps({"file": str(doc1), "embedding": [1, 0]})
    )
    doc2 = tmp_path / "doc2.md"
    doc2.write_text("beta")
    (tmp_path / "doc2.md.embedding.json").write_text(
        json.dumps({"file": str(doc2), "embedding": [0, 1]})
    )
    return doc1, doc2


def test_query_with_ask(monkeypatch, tmp_path):
    doc1, _ = _setup_store(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "test")

    fake_client = MagicMock()
    fake_client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=[1, 0])]
    )
    monkeypatch.setattr(query_module, "OpenAI", lambda api_key, base_url: fake_client)

    fake_resp = SimpleNamespace(output_text="final answer")
    mock_create = MagicMock(return_value=fake_resp)
    monkeypatch.setattr(query_module, "create_response", mock_create)

    runner = CliRunner()
    result = runner.invoke(
        query_module.app,
        ["--ask", "--model", "gpt-4o", "--k", "1", str(tmp_path), "what?"],
    )
    assert result.exit_code == 0
    mock_create.assert_called_once()
    _, kwargs = mock_create.call_args
    assert kwargs["model"] == "gpt-4o"
    prompt = kwargs["texts"]
    assert "what?" in prompt
    assert "alpha" in prompt
    assert "beta" not in prompt
    assert "final answer" in result.stdout
    assert str(doc1) in result.stdout


def test_query_without_ask(monkeypatch, tmp_path):
    doc1, doc2 = _setup_store(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "test")

    fake_client = MagicMock()
    fake_client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=[1, 0])]
    )
    monkeypatch.setattr(query_module, "OpenAI", lambda api_key, base_url: fake_client)

    mock_create = MagicMock()
    monkeypatch.setattr(query_module, "create_response", mock_create)

    runner = CliRunner()
    result = runner.invoke(query_module.app, ["--k", "2", str(tmp_path), "what?"])
    assert result.exit_code == 0
    assert "doc1.md" in result.stdout
    assert "doc2.md" in result.stdout
    mock_create.assert_not_called()
