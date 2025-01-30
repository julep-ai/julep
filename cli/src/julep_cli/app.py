from typing import Annotated

import typer
from rich.console import Console
from trogon.typer import init_tui

# Global state
console = Console()
error_console = Console(stderr=True)


# Initialize typer app
app = typer.Typer(
    name="julep",
    help="Command line interface for the Julep platform",
    no_args_is_help=True,
    pretty_exceptions_short=True,
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
            console.print(f"julep CLI version [green]{v}[/green]")
        except:
            error_console.print("[red]julep CLI version unknown[/red]")
            raise typer.Exit(1)

        raise typer.Exit


def no_color_callback(value: bool) -> bool:
    global console, error_console
    if value:
        console = Console(color_system=None)
        error_console = Console(color_system=None, stderr=True)

    return value


def quiet_callback(value: bool) -> bool:
    console.quiet = value

    return value


@app.callback()
def main(
    no_color: Annotated[
        bool,
        typer.Option(
            "--no-color",
            help="Disable colored output",
            callback=no_color_callback,
            is_eager=True,
        ),
    ] = not bool(console.color_system),
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress all output except errors and explicitly requested data",
            callback=quiet_callback,
            is_eager=True,
        ),
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
):
    """
    Julep CLI - Command line interface for the Julep platform
    """
