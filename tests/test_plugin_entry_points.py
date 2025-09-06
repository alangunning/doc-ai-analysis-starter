import importlib
import sys
import types

import typer
from importlib.metadata import EntryPoint
from typer.testing import CliRunner


def test_dummy_plugin_trust_required(monkeypatch, tmp_path):
    dummy = types.ModuleType("dummy_plugin")
    dummy.app = typer.Typer()
    monkeypatch.setitem(sys.modules, "dummy_plugin", dummy)

    ep = EntryPoint(name="dummy", value="dummy_plugin:app", group="doc_ai.plugins")

    import importlib.metadata as metadata
    original = metadata.entry_points
    monkeypatch.setattr(metadata, "entry_points", lambda group=None: [ep])

    monkeypatch.setenv("DOC_AI_TRUSTED_PLUGINS", "")
    import doc_ai.cli as cli
    importlib.reload(cli)
    cli._LOADED_PLUGINS.clear()
    monkeypatch.setattr(cli, "read_configs", lambda: ({}, {}, {}))

    cli._register_plugins()
    assert "dummy" not in cli._LOADED_PLUGINS

    monkeypatch.setattr(cli, "read_configs", lambda: ({}, {}, {"DOC_AI_TRUSTED_PLUGINS": "dummy"}))
    cli._register_plugins()
    assert "dummy" in cli._LOADED_PLUGINS
    assert cli._LOADED_PLUGINS["dummy"] is dummy.app

    monkeypatch.setattr(metadata, "entry_points", original)
    importlib.reload(cli)
    monkeypatch.delitem(sys.modules, "dummy_plugin", raising=False)
