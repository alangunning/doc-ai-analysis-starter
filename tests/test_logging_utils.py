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
    openai_token = "sk-" + "a" * 20
    github_token = "ghp_" + "b" * 36
    secret = f"{openai_token} and {github_token}"
    logger.warning("credentials: %s", secret)
    text = log_path.read_text()

    expected_openai = (
        openai_token[:4] + "*" * (len(openai_token) - 8) + openai_token[-4:]
    )
    expected_github = (
        github_token[:4] + "*" * (len(github_token) - 8) + github_token[-4:]
    )

    assert expected_openai in text
    assert expected_github in text
    assert openai_token not in text
    assert github_token not in text
