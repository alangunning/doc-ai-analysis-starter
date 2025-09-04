from importlib import util
from pathlib import Path

import doc_ai.cli as cli_module
from doc_ai.cli import convert_path as cli_convert_path
from doc_ai.converter import convert_path as shared_convert_path


def _load_script(name: str):
    script_path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = util.spec_from_file_location(name, script_path)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_cli_uses_shared_function() -> None:
    assert cli_convert_path is shared_convert_path


def test_convert_script_invokes_cli(monkeypatch) -> None:
    called: dict[str, object] = {}

    def fake_app(*, prog_name=None, args=None, **kwargs):
        called["prog_name"] = prog_name
        called["args"] = args

    monkeypatch.setattr(cli_module, "app", fake_app)
    module = _load_script("convert")
    module.main(["--help"])
    assert called["args"][0] == "convert"
    assert called["args"][1:] == ["--help"]
