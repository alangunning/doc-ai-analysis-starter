from doc_ai.cli import utils


def test_load_env_defaults_fallback(monkeypatch):
    utils.load_env_defaults.cache_clear()
    monkeypatch.setattr(utils.Path, "exists", lambda self: False)
    defaults = utils.load_env_defaults()
    assert defaults == utils.DEFAULT_ENV_VARS
    utils.load_env_defaults.cache_clear()
