from pathlib import Path
import time

from typer.testing import CliRunner

from doc_ai.cli import app
from doc_ai.cli.convert import download_and_convert


class DummyResp:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def raise_for_status(self) -> None:  # pragma: no cover - no errors
        return

    def iter_content(
        self, chunk_size: int = 8192
    ):  # pragma: no cover - simple iterator
        yield self.data

    def close(self) -> None:  # pragma: no cover - nothing to close
        return


def _mock_http_get(url_map):
    def _get(url, stream=True):  # noqa: D401 - mimics http_get signature
        return DummyResp(url_map[url])

    return _get


def test_convert_downloads_multiple_urls(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    urls = {
        "http://example.com/a.txt": b"a",
        "http://example.com/b.txt": b"b",
    }
    monkeypatch.setattr("doc_ai.cli.convert.http_get", _mock_http_get(urls))
    called = []

    def fake_convert_path(path, fmts, force=False):
        called.append(Path(path))
        return {}

    monkeypatch.setattr("doc_ai.cli.convert_path", fake_convert_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "convert",
            "--doc-type",
            "reports",
            "--url",
            "http://example.com/a.txt",
            "--url",
            "http://example.com/b.txt",
        ],
    )
    assert result.exit_code == 0, result.output
    dest = Path("data/reports")
    assert (dest / "a.txt").read_bytes() == b"a"
    assert (dest / "b.txt").read_bytes() == b"b"
    assert called == [dest]


def test_add_url_command(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "doc_ai.cli.convert.http_get", _mock_http_get({"http://x/y.txt": b"y"})
    )
    called = []

    def fake_convert_path(path, fmts, force=False):
        called.append(Path(path))
        return {}

    monkeypatch.setattr("doc_ai.cli.convert_path", fake_convert_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["add", "url", "http://x/y.txt", "--doc-type", "letters"],
    )
    assert result.exit_code == 0, result.output
    dest = Path("data/letters")
    assert (dest / "y.txt").read_bytes() == b"y"
    assert called == [dest]


def test_add_urls_command(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    urls = {
        "http://example.com/a.txt": b"a",
        "http://example.com/b.txt": b"b",
    }
    monkeypatch.setattr("doc_ai.cli.convert.http_get", _mock_http_get(urls))
    called = []

    def fake_convert_path(path, fmts, force=False):
        called.append(Path(path))
        return {}

    monkeypatch.setattr("doc_ai.cli.convert_path", fake_convert_path)

    url_file = tmp_path / "urls.txt"
    url_file.write_text(
        "\n".join(
            [
                "http://example.com/a.txt",
                "not-a-url",
                "http://example.com/a.txt",
                "http://example.com/b.txt",
            ]
        )
    )

    runner = CliRunner()
    result = runner.invoke(app, ["add", "urls", str(url_file), "--doc-type", "letters"])
    assert result.exit_code == 0, result.output
    dest = Path("data/letters")
    assert (dest / "a.txt").read_bytes() == b"a"
    assert (dest / "b.txt").read_bytes() == b"b"
    assert called == [dest]


def test_urls_command(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    doc_dir = Path("data/reports")
    doc_dir.mkdir(parents=True)
    url_file = doc_dir / "urls.txt"
    url_file.write_text("http://a\nhttp://b\n")

    class DummyPrompt:
        def __init__(self, response: str) -> None:
            self.response = response

        def ask(self) -> str:
            return self.response
    selections = iter(["remove", "http://a", "add", "done"])

    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.questionary.select",
        lambda *a, **k: DummyPrompt(next(selections)),
    )
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.questionary.text",
        lambda *a, **k: DummyPrompt("http://c"),
    )
    called = []
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.refresh_completer", lambda: called.append(True)
    )

    runner = CliRunner()
    result = runner.invoke(app, ["urls", "--doc-type", "reports"])
    assert result.exit_code == 0, result.output
    assert url_file.read_text().splitlines() == ["http://b", "http://c"]
    assert called == [True, True]


def test_urls_bulk_delete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    doc_dir = Path("data/reports")
    doc_dir.mkdir(parents=True)
    url_file = doc_dir / "urls.txt"
    url_file.write_text("http://a\nhttp://b\n")

    class DummyPrompt:
        def __init__(self, response: str) -> None:
            self.response = response

        def ask(self) -> str:
            return self.response

    selections = iter(["remove", "http://a", "remove", "http://b", "done"])
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.questionary.select",
        lambda *a, **k: DummyPrompt(next(selections)),
    )
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.questionary.text",
        lambda *a, **k: DummyPrompt(""),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["urls", "--doc-type", "reports"])
    assert result.exit_code == 0, result.output
    assert url_file.read_text().splitlines() == []


def test_urls_add_multiple(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    doc_dir = Path("data/reports")
    doc_dir.mkdir(parents=True)
    url_file = doc_dir / "urls.txt"
    url_file.write_text("http://a\n")

    class DummyPrompt:
        def __init__(self, response: str) -> None:
            self.response = response

        def ask(self) -> str:
            return self.response

    selections = iter(["add", "done"])
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.questionary.select",
        lambda *a, **k: DummyPrompt(next(selections)),
    )
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.questionary.text",
        lambda *a, **k: DummyPrompt("http://b http://c\nnotaurl http://a"),
    )
    called = []
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.refresh_completer", lambda: called.append(True)
    )

    runner = CliRunner()
    result = runner.invoke(app, ["urls", "--doc-type", "reports"])
    assert result.exit_code == 0, result.output
    assert url_file.read_text().splitlines() == ["http://a", "http://b", "http://c"]
    assert called == [True]


def test_urls_import_action(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    doc_dir = Path("data/reports")
    doc_dir.mkdir(parents=True)
    url_file = doc_dir / "urls.txt"
    url_file.write_text("")
    import_file = tmp_path / "list.txt"
    import_file.write_text(
        "\n".join([
            "http://a",
            "notaurl",
            "http://a",
            "http://b",
        ])
    )

    class DummyPrompt:
        def __init__(self, response: str) -> None:
            self.response = response

        def ask(self) -> str:
            return self.response

    selections = iter(["import", "done"])
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.questionary.select",
        lambda *a, **k: DummyPrompt(next(selections)),
    )
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.questionary.text",
        lambda *a, **k: DummyPrompt(str(import_file)),
    )
    called = []
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.refresh_completer", lambda: called.append(True)
    )

    runner = CliRunner()
    result = runner.invoke(app, ["urls", "--doc-type", "reports"])
    assert result.exit_code == 0, result.output
    assert url_file.read_text().splitlines() == ["http://a", "http://b"]
    assert called == [True]


def test_urls_list_subcommand(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    doc_dir = Path("data/reports")
    doc_dir.mkdir(parents=True)
    url_file = doc_dir / "urls.txt"
    url_file.write_text("http://a\nhttp://b\n")
    runner = CliRunner()
    result = runner.invoke(app, ["urls", "list", "--doc-type", "reports"])
    assert result.exit_code == 0, result.output
    assert "1. http://a" in result.output
    assert "2. http://b" in result.output


def test_urls_add_subcommand(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    called = []
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.refresh_completer", lambda: called.append(True)
    )
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "urls",
            "add",
            "--doc-type",
            "reports",
            "--url",
            "http://a",
            "--url",
            "notaurl",
            "--url",
            "http://a",
            "--url",
            "http://b",
        ],
    )
    assert result.exit_code == 0, result.output
    url_file = Path("data/reports/urls.txt")
    assert url_file.read_text().splitlines() == ["http://a", "http://b"]
    assert called == [True]


def test_urls_import_subcommand(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    called = []
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.refresh_completer", lambda: called.append(True)
    )
    import_file = tmp_path / "list.txt"
    import_file.write_text(
        "\n".join(["http://a", "notaurl", "http://a", "http://b"])
    )
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "urls",
            "import",
            "--doc-type",
            "reports",
            "--file",
            str(import_file),
        ],
    )
    assert result.exit_code == 0, result.output
    url_file = Path("data/reports/urls.txt")
    assert url_file.read_text().splitlines() == ["http://a", "http://b"]
    assert called == [True]


def test_urls_remove_subcommand(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    doc_dir = Path("data/reports")
    doc_dir.mkdir(parents=True)
    url_file = doc_dir / "urls.txt"
    url_file.write_text("http://a\nhttp://b\n")
    called = []
    monkeypatch.setattr(
        "doc_ai.cli.manage_urls.refresh_completer", lambda: called.append(True)
    )
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "urls",
            "remove",
            "--doc-type",
            "reports",
            "--url",
            "http://a",
        ],
    )
    assert result.exit_code == 0, result.output
    assert url_file.read_text().splitlines() == ["http://b"]
    assert called == [True]


def test_add_url_rejects_invalid(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(
        app, ["add", "url", "notaurl", "--doc-type", "letters"], input=""
    )
    assert result.exit_code != 0


def test_add_url_prompts_for_doc_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (Path("data/letters")).mkdir(parents=True)
    monkeypatch.setattr(
        "doc_ai.cli.convert.http_get", _mock_http_get({"http://x/y.txt": b"y"})
    )
    called = []

    def fake_convert_path(path, fmts, force=False):
        called.append(Path(path))
        return {}

    monkeypatch.setattr("doc_ai.cli.convert_path", fake_convert_path)

    class DummyPrompt:
        def __init__(self, response: str) -> None:
            self.response = response

        def ask(self) -> str:
            return self.response

    monkeypatch.setattr(
        "doc_ai.cli.add.questionary.select", lambda *a, **k: DummyPrompt("letters")
    )

    runner = CliRunner()
    result = runner.invoke(app, ["add", "url", "http://x/y.txt"])
    assert result.exit_code == 0, result.output
    assert called == [Path("data/letters")]


def test_download_sanitizes_and_uniquifies(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    urls = {
        "http://example.com/Hello World!.txt": b"a",
        "http://example.com/hello-world!.txt": b"b",
    }
    monkeypatch.setattr("doc_ai.cli.convert.http_get", _mock_http_get(urls))
    called = []

    def fake_convert_path(path, fmts, force=False):
        called.append(Path(path))
        return {}

    monkeypatch.setattr("doc_ai.cli.convert_path", fake_convert_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "convert",
            "--doc-type",
            "reports",
            "--url",
            "http://example.com/Hello World!.txt",
            "--url",
            "http://example.com/hello-world!.txt",
        ],
    )
    assert result.exit_code == 0, result.output
    dest = Path("data/reports")
    assert (dest / "hello-world.txt").read_bytes() == b"a"
    assert (dest / "hello-world-1.txt").read_bytes() == b"b"
    assert called == [dest]


def test_download_parallel_execution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    urls = ["http://example.com/a.txt", "http://example.com/b.txt"]

    def slow_http_get(u, stream=True):
        time.sleep(0.2)
        return DummyResp(b"x")

    monkeypatch.setattr("doc_ai.cli.convert.http_get", slow_http_get)
    monkeypatch.setattr("doc_ai.cli.convert_path", lambda path, fmts, force=False: {})

    start = time.perf_counter()
    download_and_convert(urls, "reports", [], False)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.35
