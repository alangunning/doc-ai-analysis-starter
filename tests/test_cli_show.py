from typer.testing import CliRunner

from doc_ai.cli import app


def test_show_doc_types_and_topics(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    (data_dir / "invoice").mkdir(parents=True)
    (data_dir / "invoice" / "analysis_sales.prompt.yaml").write_text("")
    (data_dir / "report").mkdir()
    (data_dir / "report" / "report.analysis.finance.prompt.yaml").write_text("")
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["show", "doc-types"])
    assert result.exit_code == 0
    out = result.stdout.splitlines()
    assert {"invoice", "report"} <= set(out)

    result = runner.invoke(app, ["show", "topics"])
    assert result.exit_code == 0
    out = result.stdout.splitlines()
    assert {"sales", "finance"} <= set(out)
