import sys
from importlib import util
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from doc_ai.cli import convert_path as cli_convert_path
from doc_ai.converter import convert_path as shared_convert_path


def _load_script_convert_path() -> object:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "convert.py"
    spec = util.spec_from_file_location("convert_script", script_path)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.convert_path


def test_entry_points_use_shared_function() -> None:
    script_convert_path = _load_script_convert_path()
    assert cli_convert_path is shared_convert_path
    assert script_convert_path is shared_convert_path
