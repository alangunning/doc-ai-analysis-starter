import logging

from doc_ai.github import prompts


def test_github_logs_redact_tokens(caplog):
    secret = "ghp_" + "x" * 40
    with caplog.at_level(logging.INFO):
        prompts.logger.info("token: %s", secret)
    assert "ghp_" not in caplog.text
    assert "<redacted>" in caplog.text

