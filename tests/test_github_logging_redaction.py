import logging

from doc_ai.github import prompts


def test_github_logs_redact_tokens(caplog):
    secret = "ghp_" + "x" * 40
    expected = secret[:4] + "*" * (len(secret) - 8) + secret[-4:]
    with caplog.at_level(logging.INFO):
        prompts.logger.info("token: %s", secret)
    assert expected in caplog.text
    assert secret not in caplog.text

