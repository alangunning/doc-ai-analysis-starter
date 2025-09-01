from pathlib import Path
from unittest.mock import MagicMock, patch

from doc_ai.converter import OutputFormat, convert_path, document_converter as dc


def test_convert_path_returns_results(tmp_path):
    input_file = tmp_path / "input.pdf"
    input_file.write_bytes(b"pdf")

    with patch("doc_ai.converter.document_converter._DoclingConverter") as MockConverter:
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
        content = b"data"

        def raise_for_status(self):
            pass

    # ensure download goes into tmp_path
    monkeypatch.setattr("doc_ai.converter.path.tempfile.mkdtemp", lambda: str(tmp_path))
    monkeypatch.setattr("doc_ai.converter.path.requests.get", lambda u, timeout=30: DummyResp())

    def fake_convert_files(src, outputs, return_status=True):
        for out in outputs.values():
            out.write_text("converted", encoding="utf-8")
        return outputs, "OK"

    monkeypatch.setattr("doc_ai.converter.path.convert_files", fake_convert_files)

    result = convert_path(url, [OutputFormat.TEXT])

    downloaded = tmp_path / "file.pdf"
    assert downloaded.read_bytes() == b"data"
    assert downloaded in result

    from doc_ai.metadata import load_metadata

    meta = load_metadata(downloaded)
    inputs = meta.extra["inputs"]["conversion"]
    assert inputs["source_url"] == url
    assert inputs["source"] == str(downloaded)


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
