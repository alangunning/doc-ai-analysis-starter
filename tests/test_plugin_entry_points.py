import hashlib
import importlib
import sys
import types

import typer


def test_dummy_plugin_trust_required(monkeypatch, tmp_path):
    dummy = types.ModuleType("dummy_plugin")
    dummy.app = typer.Typer()
    monkeypatch.setitem(sys.modules, "dummy_plugin", dummy)

    class DummyDist:
        def __init__(self, path):
            self.metadata = {"Name": "dummy"}
            self.version = "1.0"
            self._path = path

        def locate_file(self, *_):  # pragma: no cover - trivial
            return self._path

    class DummyEntryPoint:
        name = "dummy"
        value = "dummy_plugin:app"
        group = "doc_ai.plugins"
        dist = DummyDist(tmp_path)

        def load(self):  # pragma: no cover - trivial
            return dummy.app

    import importlib.metadata as metadata

    original = metadata.entry_points
    monkeypatch.setattr(
        metadata, "entry_points", lambda group=None: [DummyEntryPoint()]
    )

    import doc_ai.cli as cli

    importlib.reload(cli)
    cli._LOADED_PLUGINS.clear()
    monkeypatch.setattr(cli, "read_configs", lambda: ({}, {}, {}))

    cli._register_plugins()
    assert "dummy" not in cli._LOADED_PLUGINS

    correct_hash = hashlib.sha256(b"").hexdigest()

    # Trusted name and version but missing hash -> reject
    monkeypatch.setattr(
        cli,
        "read_configs",
        lambda: ({}, {}, {"DOC_AI_TRUSTED_PLUGINS": "dummy==1.0"}),
    )
    cli._register_plugins()
    assert "dummy" not in cli._LOADED_PLUGINS

    # Trusted with correct version and hash -> load
    monkeypatch.setattr(
        cli,
        "read_configs",
        lambda: (
            {},
            {},
            {
                "DOC_AI_TRUSTED_PLUGINS": "dummy==1.0",
                "DOC_AI_TRUSTED_PLUGIN_HASHES": f"dummy={correct_hash}",
            },
        ),
    )
    cli._register_plugins()
    assert cli._LOADED_PLUGINS["dummy"] is dummy.app

    # Version mismatch even with hash -> reject
    cli._LOADED_PLUGINS.clear()
    monkeypatch.setattr(
        cli,
        "read_configs",
        lambda: (
            {},
            {},
            {
                "DOC_AI_TRUSTED_PLUGINS": "dummy==2.0",
                "DOC_AI_TRUSTED_PLUGIN_HASHES": f"dummy={correct_hash}",
            },
        ),
    )
    cli._register_plugins()
    assert "dummy" not in cli._LOADED_PLUGINS

    # Hash mismatch -> reject
    monkeypatch.setattr(
        cli,
        "read_configs",
        lambda: (
            {},
            {},
            {
                "DOC_AI_TRUSTED_PLUGINS": "dummy==1.0",
                "DOC_AI_TRUSTED_PLUGIN_HASHES": "dummy=deadbeef",
            },
        ),
    )
    cli._register_plugins()
    assert "dummy" not in cli._LOADED_PLUGINS

    monkeypatch.setattr(metadata, "entry_points", original)
    importlib.reload(cli)
    monkeypatch.delitem(sys.modules, "dummy_plugin", raising=False)
