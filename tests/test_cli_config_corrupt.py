import logging

import doc_ai.cli as cli


def test_load_global_config_logs_warning(monkeypatch, tmp_path, caplog):
    bad = tmp_path / "config.json"
    bad.write_text("{ invalid json")
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_PATH", bad)
    with caplog.at_level(logging.WARNING, logger=cli.__name__):
        cfg = cli.load_global_config()
    assert cfg == {}
    assert any(record.levelno == logging.WARNING for record in caplog.records)
    assert str(bad) in caplog.text
