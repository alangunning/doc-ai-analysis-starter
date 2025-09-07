import os
import subprocess
import sys
import venv
from pathlib import Path


def _create_venv(path: Path) -> Path:
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(path)
    if os.name == "nt":
        return path / "Scripts" / "python.exe"
    return path / "bin" / "python"


def test_wheel_installation_includes_data_and_typing(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)],
        check=True,
        cwd=project_root,
    )

    wheel = next(dist_dir.glob("*.whl"))

    venv_dir = tmp_path / "venv"
    python = _create_venv(venv_dir)

    subprocess.run(
        [str(python), "-m", "pip", "install", "--no-deps", str(wheel)], check=True
    )

    pkg_path = Path(
        subprocess.check_output(
            [
                str(python),
                "-c",
                (
                    "import importlib.util, pathlib; "
                    "spec = importlib.util.find_spec('doc_ai'); "
                    "print(pathlib.Path(spec.origin).parent)"
                ),
            ],
            text=True,
        ).strip()
    )
    assert (pkg_path / "py.typed").is_file()

    data_dir = venv_dir / "data"
    assert data_dir.is_dir() and any(data_dir.iterdir())
