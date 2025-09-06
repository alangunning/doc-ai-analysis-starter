import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from doc_ai.cli import app


@pytest.mark.parametrize(
    "value, message",
    [
        (None, "Missing required environment variable: EMBED_DIMENSIONS"),
        ("abc", "EMBED_DIMENSIONS must be a positive integer; got abc"),
        ("0", "EMBED_DIMENSIONS must be a positive integer; got 0"),
        ("-5", "EMBED_DIMENSIONS must be a positive integer; got -5"),
    ],
)
def test_cli_rejects_invalid_embed_dimensions(monkeypatch, tmp_path, value, message):
    runner = CliRunner()
    if value is None:
        monkeypatch.delenv("EMBED_DIMENSIONS", raising=False)
    else:
        monkeypatch.setenv("EMBED_DIMENSIONS", value)
    result = runner.invoke(app, ["embed", str(tmp_path)])
    assert result.exit_code != 0
    assert message in result.output


@pytest.mark.parametrize(
    "value, message",
    [
        (None, "Missing required environment variable: EMBED_DIMENSIONS"),
        ("abc", "EMBED_DIMENSIONS must be a positive integer; got abc"),
        ("0", "EMBED_DIMENSIONS must be a positive integer; got 0"),
        ("-5", "EMBED_DIMENSIONS must be a positive integer; got -5"),
    ],
)
def test_vector_module_raises_runtime_error(monkeypatch, value, message):
    if value is None:
        monkeypatch.delenv("EMBED_DIMENSIONS", raising=False)
    else:
        monkeypatch.setenv("EMBED_DIMENSIONS", value)
    import sys

    original = sys.modules.pop("doc_ai.github.vector", None)
    with pytest.raises(RuntimeError, match=message):
        importlib.import_module("doc_ai.github.vector")
    if original is not None:
        sys.modules["doc_ai.github.vector"] = original


def test_build_vector_store_uses_dimensions_when_positive(tmp_path, monkeypatch):
    md = tmp_path / "doc.md"
    md.write_text("content")
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    monkeypatch.setenv("EMBED_DIMENSIONS", "64")
    vector = importlib.import_module("doc_ai.github.vector")
    importlib.reload(vector)
    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=[0.1])]
    )
    with patch("doc_ai.github.vector.OpenAI", return_value=mock_client):
        vector.build_vector_store(tmp_path)
    kwargs = mock_client.embeddings.create.call_args.kwargs
    assert kwargs["dimensions"] == 64
