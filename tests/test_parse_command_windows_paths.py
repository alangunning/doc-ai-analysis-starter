import click
from click.testing import CliRunner
from doc_ai.cli.interactive import _parse_command

@click.command()
@click.argument("path")
def show(path: str) -> None:
    """Echo the provided path."""
    click.echo(path)


def test_parse_command_windows_path_roundtrip():
    win_path = r"C:\\Program Files\\Doc AI\\input file.txt"
    command = f'show "{win_path}"'
    args = _parse_command(command)
    assert args == ["show", win_path]
    runner = CliRunner()
    result = runner.invoke(show, [win_path])
    assert result.exit_code == 0
    assert result.stdout.strip() == win_path
