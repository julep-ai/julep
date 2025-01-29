import typer
from trogon.typer import init_tui

# Initialize typer app
app = typer.Typer(
    name="julep",
    help="Command line interface for the Julep platform",
    no_args_is_help=True,
    pretty_exceptions_short=False,
)

init_tui(app)

# Initialize subcommands
agents_app = typer.Typer(help="Manage AI agents")
tasks_app = typer.Typer(help="Manage tasks")
tools_app = typer.Typer(help="Manage tools")
import_app = typer.Typer(help="Import entities from the Julep platform")
executions_app = typer.Typer(help="Manage executions")

app.add_typer(agents_app, name="agents")
app.add_typer(tasks_app, name="tasks")
app.add_typer(tools_app, name="tools")
app.add_typer(import_app, name="import")
app.add_typer(executions_app, name="executions")


# Version command
def version_callback(value: bool):
    if value:
        from importlib.metadata import version

        try:
            v = version("julep-cli")
            typer.echo(f"julep CLI version {v}")
        except:
            typer.echo("julep CLI version unknown")
        raise typer.Exit


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    """
    Julep CLI - Command line interface for the Julep platform
    """
