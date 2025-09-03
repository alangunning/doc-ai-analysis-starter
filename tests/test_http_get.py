from doc_ai.utils import http_get


def test_http_get_closes_session(monkeypatch):
    closed = {"value": False}

    class DummyResponse:
        pass

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
    assert closed["value"]
