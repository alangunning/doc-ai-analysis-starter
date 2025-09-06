from concurrent.futures import Future
from types import SimpleNamespace

from doc_ai.github import vector


def test_build_vector_store_uses_workers(tmp_path, monkeypatch):
    md = tmp_path / "doc.md"
    md.write_text("content")
    monkeypatch.setenv("GITHUB_TOKEN", "tok")

    captured = {}

    class DummyExecutor:
        def __init__(self, max_workers):
            captured["max_workers"] = max_workers

        def submit(self, fn, *args, **kwargs):
            fn(*args, **kwargs)
            fut = Future()
            fut.set_result(None)
            return fut

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    mock_client = SimpleNamespace(
        embeddings=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.1])]
            )
        )
    )

    monkeypatch.setattr(vector, "ThreadPoolExecutor", DummyExecutor)
    monkeypatch.setattr(
        "doc_ai.github.vector.OpenAI", lambda api_key, base_url: mock_client
    )

    vector.build_vector_store(tmp_path, workers=7)
    assert captured["max_workers"] == 7
