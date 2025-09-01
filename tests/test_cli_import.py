import subprocess
import sys
from pathlib import Path

def test_cli_help_runs():
    script = Path(__file__).resolve().parents[1] / "doc_ai" / "cli.py"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Orchestrate conversion, validation, analysis and embedding generation." in result.stdout
