from unittest.mock import MagicMock

from doc_ai.cli.utils import load_env_defaults


def test_load_env_defaults_is_cached(monkeypatch):
    load_env_defaults.cache_clear()
    mock = MagicMock(return_value={"A": "1"})
    monkeypatch.setattr("doc_ai.cli.utils.dotenv_values", mock)
    first = load_env_defaults()
    second = load_env_defaults()
    assert first is second
    mock.assert_called_once()
    load_env_defaults.cache_clear()
