import logging

from doc_ai.logging import RedactFilter


def test_redact_filter_reads_config(monkeypatch):
    record = logging.LogRecord("test", logging.INFO, "", 0, "foo123", None, None)
    RedactFilter().filter(record)
    assert "foo123" in record.msg

    monkeypatch.setenv("LOG_REDACTION_PATTERNS", r"foo\d+")
    filt = RedactFilter()
    record = logging.LogRecord("test", logging.INFO, "", 0, "foo123", None, None)
    filt.filter(record)
    assert "<redacted>" in record.msg
