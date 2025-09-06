import sys
import importlib


def test_config_wizard_collects_values(monkeypatch):
    cli = importlib.reload(importlib.import_module("doc_ai.cli"))
    captured: dict[str, object] = {}

    def fake_set_pairs(ctx, pairs, use_global):
        captured["pairs"] = pairs
        captured["global"] = use_global

    monkeypatch.setattr(cli.config_cmd, "_set_pairs", fake_set_pairs)
    monkeypatch.setattr(cli.config_cmd, "KNOWN_KEYS", {"FOO", "BAR"})
    monkeypatch.setattr(
        cli.config_cmd, "load_env_defaults", lambda: {"FOO": "bar", "BAR": None}
    )

    answers = iter(["", "baz"])

    class Dummy:
        def __init__(self, ans):
            self.ans = ans

        def ask(self):
            return self.ans

    monkeypatch.setattr(
        "questionary.text", lambda message, default="": Dummy(next(answers))
    )
    monkeypatch.setenv("INTERACTIVE", "true")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)

    ctx = type("C", (), {"obj": {}})()
    cli.config_cmd.wizard(ctx)
    assert captured["pairs"] == ["FOO=baz"]
