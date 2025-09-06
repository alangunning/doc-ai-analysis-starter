from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from doc_ai.github import vector


@pytest.mark.parametrize("value", ["0", "-5", "abc"])
def test_build_vector_store_ignores_bad_embed_dimensions(tmp_path, monkeypatch, value):
    md = tmp_path / "doc.md"
    md.write_text("content")
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    monkeypatch.setattr(vector, "EMBED_DIMENSIONS", value)
    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=[0.1])]
    )
    with patch("doc_ai.github.vector.OpenAI", return_value=mock_client):
        vector.build_vector_store(tmp_path)
    kwargs = mock_client.embeddings.create.call_args.kwargs
    assert "dimensions" not in kwargs


def test_build_vector_store_uses_dimensions_when_positive(tmp_path, monkeypatch):
    md = tmp_path / "doc.md"
    md.write_text("content")
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    monkeypatch.setattr(vector, "EMBED_DIMENSIONS", "64")
    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=[0.1])]
    )
    with patch("doc_ai.github.vector.OpenAI", return_value=mock_client):
        vector.build_vector_store(tmp_path)
    kwargs = mock_client.embeddings.create.call_args.kwargs
    assert kwargs["dimensions"] == 64
