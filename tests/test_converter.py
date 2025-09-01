import json
from unittest.mock import MagicMock, patch

from doc_ai.converter import OutputFormat, convert_files


def test_convert_files_writes_outputs(tmp_path):
    input_file = tmp_path / "input.pdf"
    input_file.write_bytes(b"pdf")

    outputs = {
        OutputFormat.TEXT: tmp_path / "out.txt",
        OutputFormat.JSON: tmp_path / "out.json",
    }

    with patch("doc_ai.converter.document_converter._DoclingConverter") as MockConverter:
        from doc_ai.converter import document_converter as dc
        dc._converter_instance = None
        class DummyDoc:
            def export_to_text(self):
                return "plain"

            def export_to_dict(self):
                return {"a": 1}

        class DummyResult:
            document = DummyDoc()
            status = "SUCCESS"

        MockConverter.return_value.convert.return_value = DummyResult()

        written, status = convert_files(input_file, outputs, return_status=True)

    assert written == outputs
    assert status == "SUCCESS"
    assert outputs[OutputFormat.TEXT].read_text() == "plain"
    assert json.loads(outputs[OutputFormat.JSON].read_text()) == {"a": 1}


def test_convert_files_return_status_optional(tmp_path):
    input_file = tmp_path / "input.pdf"
    input_file.write_bytes(b"pdf")

    outputs = {OutputFormat.TEXT: tmp_path / "out.txt"}

    with patch("doc_ai.converter.document_converter._DoclingConverter") as MockConverter:
        from doc_ai.converter import document_converter as dc
        dc._converter_instance = None

        class DummyDoc:
            def export_to_text(self):
                return "plain"

        class DummyResult:
            document = DummyDoc()
            status = "SUCCESS"

        MockConverter.return_value.convert.return_value = DummyResult()

        written = convert_files(input_file, outputs)

    assert written == outputs
    assert outputs[OutputFormat.TEXT].read_text() == "plain"
