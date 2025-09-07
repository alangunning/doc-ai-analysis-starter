import subprocess
import sys


def test_wheel_installation(tmp_path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(dist_dir),
        ],
        check=True,
    )
    wheel = next(dist_dir.glob("*.whl"))

    venv_dir = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    pip = venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
    subprocess.run([str(pip), "install", "--no-deps", str(wheel)], check=True)

    py_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
    lib = (
        venv_dir
        / ("Lib" if sys.platform == "win32" else "lib")
        / py_ver
        / "site-packages"
    )
    pkg = lib / "doc_ai"

    assert (pkg / "py.typed").is_file()
    data_file = pkg / "data" / "sec-form-10q" / "sec-form-10q.analysis.prompt.yaml"
    assert data_file.is_file()
