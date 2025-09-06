import importlib
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

def test_default_doc_type_and_topic(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        monkeypatch.setenv("XDG_CONFIG_HOME", str(Path("xdg")))
        cli = importlib.reload(importlib.import_module("doc_ai.cli"))
        monkeypatch.setattr(cli, "ENV_FILE", ".env")

        # Set default document type
        res = runner.invoke(cli.app, ["config", "default-doc-type", "sample"])
        assert res.exit_code == 0

        called: dict[str, str] = {}

        def fake_convert(urls, doc_type, fmts, force):
            called["doc_type"] = doc_type

        with patch("doc_ai.cli.add.download_and_convert", fake_convert):
            res = runner.invoke(cli.app, ["add", "url", "https://example.com"])
        assert res.exit_code == 0
        assert called["doc_type"] == "sample"

        # Clear default doc type
        res = runner.invoke(cli.app, ["config", "default-doc-type"])
        assert res.exit_code == 0

        with patch("doc_ai.cli.add.download_and_convert", fake_convert):
            res = runner.invoke(cli.app, ["add", "url", "https://example.com"])
        assert res.exit_code != 0

        # Set default topic
        res = runner.invoke(cli.app, ["config", "default-topic", "biology"])
        assert res.exit_code == 0

        Path("doc.converted.md").write_text("test")
        captured: dict[str, str | None] = {}

        def fake_analyze_doc(
            markdown_doc,
            prompt,
            output,
            model,
            base_model_url,
            require_json,
            show_cost,
            estimate,
            topic=None,
            force=False,
        ):
            captured["topic"] = topic

        with patch("doc_ai.cli.analyze.analyze_doc", fake_analyze_doc):
            res = runner.invoke(cli.app, ["analyze", "doc.converted.md"])
        assert res.exit_code == 0
        assert captured["topic"] == "biology"

        # Clear default topic
        res = runner.invoke(cli.app, ["config", "default-topic"])
        assert res.exit_code == 0

        captured.clear()
        with patch("doc_ai.cli.analyze.analyze_doc", fake_analyze_doc):
            res = runner.invoke(cli.app, ["analyze", "doc.converted.md"])
        assert res.exit_code == 0
        assert captured["topic"] is None
