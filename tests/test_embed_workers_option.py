from typer.testing import CliRunner

from doc_ai.cli import app


def test_embed_workers_option(monkeypatch, tmp_path):
    captured = {}

    def fake_build_vector_store(src, *, fail_fast=False, workers=1):
        captured["src"] = src
        captured["workers"] = workers

    monkeypatch.setattr("doc_ai.cli.embed.build_vector_store", fake_build_vector_store)

    runner = CliRunner()
    result = runner.invoke(app, ["embed", "--workers", "3", str(tmp_path)])
    assert result.exit_code == 0
    assert captured["src"] == tmp_path
    assert captured["workers"] == 3
