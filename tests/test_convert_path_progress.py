from doc_ai.converter import OutputFormat, convert_path


def test_convert_path_uses_progress(monkeypatch, tmp_path):
    src = tmp_path / "docs"
    src.mkdir()
    for name in ["a.pdf", "b.pdf"]:
        (src / name).write_bytes(b"pdf")

    calls = {"add": 0, "adv": 0}

    class DummyProgress:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

        def add_task(self, *a, **k):
            calls["add"] += 1
            return 1

        def advance(self, *a, **k):
            calls["adv"] += 1

    monkeypatch.setattr(
        "doc_ai.converter.path.Progress", lambda *a, **k: DummyProgress()
    )
    monkeypatch.setattr(
        "doc_ai.converter.path.convert_files", lambda *a, **k: ({}, None)
    )

    convert_path(src, [OutputFormat.TEXT], force=True)

    assert calls["add"] == 1
    assert calls["adv"] == 2
