from pathlib import Path
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
        mock_doc = MagicMock()
        mock_doc.export_to_text.return_value = "plain"
        mock_doc.export_to_dict.return_value = {"a": 1}
        MockConverter.return_value.convert.return_value.document = mock_doc

        written = convert_files(input_file, outputs)

    assert written == outputs
    assert outputs[OutputFormat.TEXT].read_text() == "plain"
    assert json.loads(outputs[OutputFormat.JSON].read_text()) == {"a": 1}
