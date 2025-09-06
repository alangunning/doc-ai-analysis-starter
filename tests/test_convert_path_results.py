from pathlib import Path
from unittest.mock import MagicMock, patch

from doc_ai.converter import OutputFormat, convert_path
from doc_ai.converter import document_converter as dc


def test_convert_path_returns_results(tmp_path):
    input_file = tmp_path / "input.pdf"
    input_file.write_bytes(b"pdf")

    with (
        patch("doc_ai.converter.document_converter._DoclingConverter") as MockConverter,
        patch("doc_ai.converter.document_converter._ensure_models_downloaded"),
    ):
        dc._converter_instance = None
        mock_doc = MagicMock()
        mock_doc.export_to_text.return_value = "plain"
        MockConverter.return_value.convert.return_value.document = mock_doc
        MockConverter.return_value.convert.return_value.status = "SUCCESS"

        results = convert_path(input_file, [OutputFormat.TEXT])

    assert input_file in results
    written, status = results[input_file]
    assert status == "SUCCESS"
    assert written[OutputFormat.TEXT].read_text() == "plain"


def test_convert_path_downloads_url_and_records_metadata(tmp_path, monkeypatch):
    url = "https://example.com/file.pdf"

    class DummyResp:
        def __init__(self):
            self.closed = False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            yield b"data"

        def close(self):
            self.closed = True

    class DummyTempDir:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return str(self.path)

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(
        "doc_ai.converter.path.TemporaryDirectory", lambda: DummyTempDir(tmp_path)
    )
    resp_obj = DummyResp()

    def fake_http_get(u, **kwargs):
        assert kwargs.get("stream") is True
        return resp_obj

    monkeypatch.setattr("doc_ai.converter.path.http_get", fake_http_get)

    def fake_convert_files(src, outputs, return_status=True):
        for out in outputs.values():
            out.write_text("converted", encoding="utf-8")
        return outputs, "OK"

    monkeypatch.setattr("doc_ai.converter.path.convert_files", fake_convert_files)

    result = convert_path(url, [OutputFormat.TEXT])

    downloaded = tmp_path / "file.pdf"
    assert downloaded.read_bytes() == b"data"
    assert downloaded in result
    assert resp_obj.closed

    from doc_ai.metadata import load_metadata

    meta = load_metadata(downloaded)
    inputs = meta.extra["inputs"]["conversion"]
    assert inputs["source_url"] == url
    assert inputs["source"] == str(downloaded)


def test_convert_path_aborts_large_download(tmp_path, monkeypatch):
    url = "https://example.com/big.pdf"

    class DummyResp:
        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            yield b"a" * 5
            yield b"b" * 5

        def close(self):
            pass

    def fake_http_get(u, **kwargs):
        assert kwargs.get("stream") is True
        return DummyResp()

    monkeypatch.setattr("doc_ai.converter.path.http_get", fake_http_get)
    called = []

    def fake_convert_files(*args, **kwargs):
        called.append(True)

    monkeypatch.setattr("doc_ai.converter.path.convert_files", fake_convert_files)

    import pytest

    with pytest.raises(ValueError, match="maximum size"):
        convert_path(url, [OutputFormat.TEXT], max_size=8)
    assert not called


def test_convert_path_skips_preconverted_files_in_directory(tmp_path, monkeypatch):
    done = tmp_path / "done.pdf"
    done.write_bytes(b"a")
    new = tmp_path / "new.pdf"
    new.write_bytes(b"b")

    calls: list[Path] = []

    def fake_convert_files(src, outputs, return_status=True):
        calls.append(src)
        for out in outputs.values():
            out.write_text("converted", encoding="utf-8")
        return outputs, "OK"

    monkeypatch.setattr("doc_ai.converter.path.convert_files", fake_convert_files)

    convert_path(done, [OutputFormat.TEXT])
    calls.clear()

    convert_path(tmp_path, [OutputFormat.TEXT])
    assert calls == [new]
