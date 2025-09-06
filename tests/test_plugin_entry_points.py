import importlib
import sys
import types

import typer
from importlib.metadata import EntryPoint


def test_dummy_plugin_loaded_via_entry_point(monkeypatch):
    dummy = types.ModuleType("dummy_plugin")
    dummy.app = typer.Typer()
    monkeypatch.setitem(sys.modules, "dummy_plugin", dummy)

    ep = EntryPoint(name="dummy", value="dummy_plugin:app", group="doc_ai.plugins")

    import importlib.metadata as metadata
    original = metadata.entry_points
    monkeypatch.setattr(metadata, "entry_points", lambda group=None: [ep])

    import doc_ai.cli as cli
    importlib.reload(cli)
    assert "dummy" in cli._LOADED_PLUGINS
    assert cli._LOADED_PLUGINS["dummy"] is dummy.app

    monkeypatch.setattr(metadata, "entry_points", original)
    importlib.reload(cli)
    monkeypatch.delitem(sys.modules, "dummy_plugin", raising=False)
