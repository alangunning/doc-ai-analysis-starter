import sys

import pytest

import doc_ai.cli as cli_module


def test_run_option_executes_batch_and_exits(monkeypatch, tmp_path):
    script = tmp_path / "init.txt"
    script.write_text("set model=gpt-4o\n")
    monkeypatch.setattr(sys, "argv", ["cli.py", "--run", str(script)])
    recorded = {}

    import doc_ai.cli.interactive as interactive_mod

    run_batch_orig = interactive_mod.run_batch

    def fake_run_batch(ctx, path):
        recorded["path"] = path
        run_batch_orig(ctx, path)
        recorded["model"] = ctx.default_map["model"]

    def fake_shell(app, init=None):
        recorded["shell"] = True

    monkeypatch.setattr(cli_module, "run_batch", fake_run_batch)
    monkeypatch.setattr(cli_module, "interactive_shell", fake_shell)

    cli_module.main()

    assert recorded["path"] == script
    assert recorded["model"] == "gpt-4o"
    assert "shell" not in recorded


def test_run_option_propagates_exit(monkeypatch, tmp_path):
    script = tmp_path / "init.txt"
    script.write_text("cd does-not-exist\n")
    monkeypatch.setattr(sys, "argv", ["cli.py", "--run", str(script)])
    with pytest.raises(SystemExit):
        cli_module.main()
