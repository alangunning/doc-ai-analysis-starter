import typer

app = typer.Typer(help="Example doc-ai plugin")

@app.command()
def hello(name: str = "World") -> None:
    """Greet someone from the plugin."""
    typer.echo(f"Hello {name}!")

