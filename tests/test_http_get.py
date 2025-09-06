from doc_ai.utils import http_get


def test_http_get_closes_session_and_raises(monkeypatch):
    closed = {"value": False}

    class DummyResponse:
        def __init__(self) -> None:
            self.raised = False

        def raise_for_status(self) -> None:
            self.raised = True

    class DummySession:
        def mount(self, *args, **kwargs):
            pass

        def get(self, url, timeout=0, **kwargs):
            return DummyResponse()

        def close(self):
            closed["value"] = True

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.close()

    monkeypatch.setattr("doc_ai.utils.requests.Session", DummySession)

    resp = http_get("http://example.com")
    assert isinstance(resp, DummyResponse)
    assert resp.raised
    assert closed["value"]


def test_http_get_suppress(monkeypatch):
    class DummyResponse:
        def __init__(self) -> None:
            self.called = False

        def raise_for_status(self) -> None:
            self.called = True

    class DummySession:
        def mount(self, *args, **kwargs):
            pass

        def get(self, url, timeout=0, **kwargs):
            return DummyResponse()

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.close()

    monkeypatch.setattr("doc_ai.utils.requests.Session", DummySession)

    resp = http_get("http://example.com", suppress_raise=True)
    assert isinstance(resp, DummyResponse)
    assert not resp.called
