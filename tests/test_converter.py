import json
import os
import threading
import time
from unittest.mock import patch

from doc_ai.converter import OutputFormat, convert_files


def test_convert_files_writes_outputs(tmp_path):
    input_file = tmp_path / "input.pdf"
    input_file.write_bytes(b"pdf")

    outputs = {
        OutputFormat.TEXT: tmp_path / "out.txt",
        OutputFormat.JSON: tmp_path / "out.json",
    }

    with (
        patch("doc_ai.converter.document_converter._DoclingConverter") as MockConverter,
        patch("doc_ai.converter.document_converter._ensure_models_downloaded"),
    ):
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

    with (
        patch("doc_ai.converter.document_converter._DoclingConverter") as MockConverter,
        patch("doc_ai.converter.document_converter._ensure_models_downloaded"),
    ):
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


def test_convert_files_passes_progress_flag(tmp_path):
    input_file = tmp_path / "input.pdf"
    input_file.write_bytes(b"pdf")

    outputs = {OutputFormat.TEXT: tmp_path / "out.txt"}

    with (
        patch("doc_ai.converter.document_converter._DoclingConverter") as MockConverter,
        patch("doc_ai.converter.document_converter._ensure_models_downloaded"),
        patch("doc_ai.converter.document_converter.Progress") as MockProgress,
        open(os.devnull, "w") as devnull,
    ):
        from doc_ai.converter import document_converter as dc

        dc._converter_instance = None
        # Use an in-memory console to avoid writing to stdout
        from rich.console import Console

        dc._console = Console(file=devnull, force_terminal=True)
        mock_progress = MockProgress.return_value.__enter__.return_value
        mock_progress.add_task.return_value = 1

        class DummyDoc:
            def export_to_text(self):
                return "plain"

        class DummyResult:
            document = DummyDoc()
            status = "SUCCESS"

        MockConverter.return_value.convert.return_value = DummyResult()

        convert_files(input_file, outputs)

        MockConverter.return_value.convert.assert_called_with(input_file, progress=True)


def test_convert_files_handles_validation_error(tmp_path):
    input_file = tmp_path / "input.pdf"
    input_file.write_bytes(b"pdf")

    outputs = {OutputFormat.TEXT: tmp_path / "out.txt"}

    with (
        patch("doc_ai.converter.document_converter._DoclingConverter") as MockConverter,
        patch("doc_ai.converter.document_converter._ensure_models_downloaded"),
        patch("doc_ai.converter.document_converter.Progress") as MockProgress,
        open(os.devnull, "w") as devnull,
    ):
        from doc_ai.converter import document_converter as dc

        dc._converter_instance = None
        from rich.console import Console

        dc._console = Console(file=devnull, force_terminal=True)
        mock_progress = MockProgress.return_value.__enter__.return_value
        mock_progress.add_task.return_value = 1

        class DummyDoc:
            def export_to_text(self):
                return "plain"

        class DummyResult:
            document = DummyDoc()
            status = "SUCCESS"

        # Create a ValidationError instance to mimic Pydantic's error
        from pydantic import BaseModel, ValidationError

        class DummyModel(BaseModel):
            x: int

        try:
            DummyModel(x="a")
        except ValidationError as e:
            val_err = e

        MockConverter.return_value.convert.side_effect = [val_err, DummyResult()]

        convert_files(input_file, outputs)

        assert MockConverter.return_value.convert.call_args_list == [
            ((input_file,), {"progress": True}),
            ((input_file,), {}),
        ]


def test_get_docling_converter_thread_safe():
    with (
        patch("doc_ai.converter.document_converter._DoclingConverter") as MockConverter,
        patch("doc_ai.converter.document_converter._ensure_models_downloaded"),
    ):
        from doc_ai.converter import document_converter as dc

        dc._converter_instance = None

        call_lock = threading.Lock()

        def side_effect():
            with call_lock:
                side_effect.calls += 1
            time.sleep(0.01)

            class Dummy:
                pass

            return Dummy()

        side_effect.calls = 0
        MockConverter.side_effect = side_effect

        results: list[object] = []

        def target():
            results.append(dc._get_docling_converter())

        threads = [threading.Thread(target=target) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert side_effect.calls == 1
        assert len({id(r) for r in results}) == 1
