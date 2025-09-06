import sys

import pytest

import doc_ai.cli as cli_module


def test_failing_subcommand_exits_with_status_one(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cli.py", "dummy"])

    def failing_app(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "app", failing_app)

    with pytest.raises(SystemExit) as excinfo:
        cli_module.main()

    assert excinfo.value.code == 1

