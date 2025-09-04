import logging

from doc_ai.logging import configure_logging


def test_log_level_and_file(tmp_path):
    log_path = tmp_path / "app.log"
    configure_logging("INFO", log_path)
    logger = logging.getLogger("test")
    logger.debug("debug message")
    logger.info("info message")
    text = log_path.read_text()
    assert "info message" in text
    assert "debug message" not in text


def test_redaction(tmp_path):
    log_path = tmp_path / "redact.log"
    configure_logging("INFO", log_path)
    logger = logging.getLogger("test")
    secret = "sk-" + "x" * 20 + " and ghp_" + "x" * 36
    logger.warning("credentials: %s", secret)
    text = log_path.read_text()
    assert "sk-" not in text
    assert "ghp_" not in text
    assert "<redacted>" in text
