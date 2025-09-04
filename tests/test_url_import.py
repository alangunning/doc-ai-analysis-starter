from pathlib import Path

from typer.testing import CliRunner

from doc_ai.cli import app


class DummyResp:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def raise_for_status(self) -> None:  # pragma: no cover - no errors
        return

    def iter_content(self, chunk_size: int = 8192):  # pragma: no cover - simple iterator
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

