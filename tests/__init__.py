import sys
from pathlib import Path

# Ensure package root is importable when running tests directly.
sys.path.append(str(Path(__file__).resolve().parents[1]))
