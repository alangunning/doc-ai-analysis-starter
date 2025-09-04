import json
from pathlib import Path

from doc_ai.cli.utils import analyze_doc


def run_json(*args, **kwargs) -> str:
    return json.dumps({"ok": True})


def run_text(*args, **kwargs) -> str:
    return "plain text"


def test_analyze_doc_json_vs_text(tmp_path: Path) -> None:
    """analyze_doc writes .analysis.json for JSON and .analysis.txt for text."""
    doc_dir = tmp_path / "docs"
    doc_dir.mkdir()

    prompt = doc_dir / "docs.analysis.prompt.yaml"
    prompt.write_text("{}")

    # JSON output case
    raw_json = doc_dir / "file-json.pdf"
    raw_json.write_text("raw")
    md_json = doc_dir / "file-json.pdf.converted.md"
    md_json.write_text("sample")
    analyze_doc(md_json, run_prompt_func=run_json)
    json_path = doc_dir / "file-json.pdf.analysis.json"
    assert json.loads(json_path.read_text()) == {"ok": True}

    # Text output case
    raw_text = doc_dir / "file-text.pdf"
    raw_text.write_text("raw")
    md_text = doc_dir / "file-text.pdf.converted.md"
    md_text.write_text("sample")
    analyze_doc(md_text, run_prompt_func=run_text)
    text_path = doc_dir / "file-text.pdf.analysis.txt"
    assert text_path.read_text() == "plain text\n"
