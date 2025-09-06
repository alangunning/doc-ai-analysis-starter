from pathlib import Path

import pytest
from typer.testing import CliRunner

from doc_ai.cli import app
from doc_ai.cli import prompt as prompt_module

runner = CliRunner()


def test_show_prompt_prints_file():
    with runner.isolated_filesystem():
        doc_dir = Path("data/sample")
        doc_dir.mkdir(parents=True)
        (doc_dir / "sample.analysis.prompt.yaml").write_text("hello world")
        result = runner.invoke(app, ["show", "prompt", "sample"])
    assert result.exit_code == 0
    assert "hello world" in result.stdout


def test_edit_prompt_invokes_editor(monkeypatch):
    called: dict[str, list[str]] = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return 0

    monkeypatch.setenv("EDITOR", "editor")
    monkeypatch.setattr(prompt_module.subprocess, "run", fake_run)
    monkeypatch.setattr(prompt_module.shutil, "which", lambda cmd: cmd)
    with runner.isolated_filesystem():
        doc_dir = Path("data/sample")
        doc_dir.mkdir(parents=True)
        prompt_path = doc_dir / "sample.analysis.prompt.yaml"
        prompt_path.write_text("x")
        result = runner.invoke(app, ["edit", "prompt", "sample"])
    assert result.exit_code == 0
    assert called["cmd"][0] == "editor"
    assert called["cmd"][1] == str(prompt_path)


def test_dangerous_editor_is_ignored(monkeypatch):
    called: dict[str, list[str]] = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return 0

    monkeypatch.setenv("EDITOR", "vim; rm -rf /")
    monkeypatch.setattr(prompt_module.subprocess, "run", fake_run)

    def fake_which(cmd: str) -> str | None:
        return cmd if cmd in {"vi", "nano"} else None

    monkeypatch.setattr(prompt_module.shutil, "which", fake_which)

    with runner.isolated_filesystem():
        doc_dir = Path("data/sample")
        doc_dir.mkdir(parents=True)
        prompt_path = doc_dir / "sample.analysis.prompt.yaml"
        prompt_path.write_text("x")
        result = runner.invoke(app, ["edit", "prompt", "sample"])
    assert result.exit_code == 0
    assert called["cmd"][0] in {"vi", "nano"}
    assert called["cmd"][1] == str(prompt_path)


def test_windows_fallback_to_notepad(monkeypatch):
    """On Windows, notepad.exe should be used if no Unix editor is found."""
    called: dict[str, list[str]] = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return 0

    def fake_which(cmd: str) -> str | None:
        return cmd if cmd == "notepad.exe" else None

    with runner.isolated_filesystem():
        doc_dir = Path("data/sample")
        doc_dir.mkdir(parents=True)
        prompt_path = doc_dir / "sample.analysis.prompt.yaml"
        prompt_path.write_text("x")

        monkeypatch.delenv("EDITOR", raising=False)
        monkeypatch.setattr(prompt_module.os, "name", "nt")
        monkeypatch.setattr(prompt_module.shutil, "which", fake_which)
        monkeypatch.setattr(prompt_module.subprocess, "run", fake_run)

        result = runner.invoke(app, ["edit", "prompt", "sample"])

    assert result.exit_code == 0
    assert called["cmd"][0] == "notepad.exe"
    assert called["cmd"][1] == str(prompt_path)


def test_no_editor_found_raises(monkeypatch):
    """If no editor is available, a RuntimeError should be raised."""
    with runner.isolated_filesystem():
        doc_dir = Path("data/sample")
        doc_dir.mkdir(parents=True)
        (doc_dir / "sample.analysis.prompt.yaml").write_text("x")

        monkeypatch.delenv("EDITOR", raising=False)
        monkeypatch.setattr(prompt_module.os, "name", "nt")
        monkeypatch.setattr(prompt_module.shutil, "which", lambda cmd: None)

        with pytest.raises(RuntimeError, match="Please edit the file manually"):
            prompt_module.edit_prompt("sample", None)
