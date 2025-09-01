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
