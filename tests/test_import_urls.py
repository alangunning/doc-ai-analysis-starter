from pathlib import Path
from functools import partial
import threading
import http.server
import socketserver

from typer.testing import CliRunner

import doc_ai.cli.import_cmd as import_cmd


def test_import_cli_handles_multiple_urls(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    with socketserver.TCPServer(("localhost", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = True
        thread.start()
        try:
            url1 = f"http://localhost:{port}/a.txt"
            url2 = f"http://localhost:{port}/b.txt"
            called: list[Path] = []

            def fake_convert_path(p, fmts, force=False):
                called.append(Path(p).resolve())
                return {}

            monkeypatch.setattr(import_cmd, "convert_path", fake_convert_path)
            work = tmp_path / "work"
            work.mkdir()
            monkeypatch.chdir(work)
            runner = CliRunner()
            result = runner.invoke(
                import_cmd.app,
                ["--url", url1, "--url", url2, "--doc-type", "reports"],
            )
            assert result.exit_code == 0
            ddir = work / "data" / "reports"
            assert (ddir / "a.txt").read_text() == "a"
            assert (ddir / "b.txt").read_text() == "b"
            assert called == [ddir / "a.txt", ddir / "b.txt"]
            urls_file = work / "urls.txt"
            assert urls_file.read_text().splitlines() == [
                f"reports\t{url1}",
                f"reports\t{url2}",
            ]
        finally:
            httpd.shutdown()
            thread.join()
