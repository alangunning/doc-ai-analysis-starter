import subprocess
import sys


def test_cli_help_runs():
    result = subprocess.run([sys.executable, "-m", "doc_ai.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Orchestrate conversion, validation, analysis and embedding generation." in result.stdout
