import importlib
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from doc_ai.cli import DEFAULT_EMBED_DIMENSIONS, _parse_embed_dimensions, app


@pytest.mark.parametrize(
    "value",
    ["abc", "0", "-5"],
)
def test_cli_warns_and_defaults_interactive(monkeypatch, caplog, value):
    runner = CliRunner()
    caplog.set_level(logging.WARNING, logger="doc_ai.cli")
    monkeypatch.setenv("EMBED_DIMENSIONS", value)
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "defaulting to" in caplog.text


@pytest.mark.parametrize(
    "value, message",
    [
        ("abc", "EMBED_DIMENSIONS must be a positive integer; got abc"),
        ("0", "EMBED_DIMENSIONS must be a positive integer; got 0"),
        ("-5", "EMBED_DIMENSIONS must be a positive integer; got -5"),
    ],
)
def test_cli_errors_invalid_embed_dimensions_non_interactive(
    monkeypatch, value, message
):
    runner = CliRunner()
    monkeypatch.setenv("EMBED_DIMENSIONS", value)
    result = runner.invoke(app, ["--no-interactive", "version"])
    assert result.exit_code != 0
    assert message in result.output


def test_parse_embed_dimensions_defaults(monkeypatch, caplog):
    monkeypatch.delenv("EMBED_DIMENSIONS", raising=False)
    caplog.set_level(logging.WARNING, logger="doc_ai.cli")
    dim = _parse_embed_dimensions(None)
    assert dim == DEFAULT_EMBED_DIMENSIONS
    assert "EMBED_DIMENSIONS not set" in caplog.text


@pytest.mark.parametrize(
    "value, message",
    [
        ("abc", "EMBED_DIMENSIONS must be a positive integer; got abc"),
        ("0", "EMBED_DIMENSIONS must be a positive integer; got 0"),
        ("-5", "EMBED_DIMENSIONS must be a positive integer; got -5"),
    ],
)
def test_vector_module_raises_runtime_error(monkeypatch, value, message):
    monkeypatch.setenv("EMBED_DIMENSIONS", value)
    import sys

    original = sys.modules.pop("doc_ai.github.vector", None)
    with pytest.raises(RuntimeError, match=message):
        importlib.import_module("doc_ai.github.vector")
    if original is not None:
        sys.modules["doc_ai.github.vector"] = original


def test_vector_module_uses_default_dimensions(monkeypatch):
    monkeypatch.delenv("EMBED_DIMENSIONS", raising=False)
    import importlib

    import doc_ai.github.vector as vector

    vector = importlib.reload(vector)
    from doc_ai.cli import DEFAULT_EMBED_DIMENSIONS

    assert vector.EMBED_DIMENSIONS == DEFAULT_EMBED_DIMENSIONS


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
