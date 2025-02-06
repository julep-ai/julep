import time
from typing import Annotated

from dateutil import tz
from rich.console import Console
from trogon.typer import init_tui
from typer import Exit, Option

from .wrapper import WrappedTyper

# Global state
console = Console()
error_console = Console(stderr=True, style="bold red")

local_tz = tz.gettz(time.tzname[time.daylight])

# Initialize typer app with -h as an alias for help
app = WrappedTyper(
    name="julep",
    help="Command line interface for the Julep platform",
    no_args_is_help=True,
    pretty_exceptions_short=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

init_tui(app)

# Initialize subcommands with help alias too
agents_app = WrappedTyper(
    help="Manage AI agents",
    context_settings={"help_option_names": ["-h", "--help"]},
)
tasks_app = WrappedTyper(
    help="Manage tasks",
    context_settings={"help_option_names": ["-h", "--help"]},
)
tools_app = WrappedTyper(
    help="Manage tools",
    context_settings={"help_option_names": ["-h", "--help"]},
)
executions_app = WrappedTyper(
    help="Manage executions",
    context_settings={"help_option_names": ["-h", "--help"]},
)

app.add_typer(agents_app, name="agents")
app.add_typer(tasks_app, name="tasks")
app.add_typer(tools_app, name="tools")
app.add_typer(executions_app, name="executions")


# Version command
def version_callback(value: bool):
    if value:
        from importlib.metadata import version

        try:
            v = version("julep-cli")
            console.print(f"julep CLI version [green]{v}[/green]", highlight=True)
        except:
            error_console.print("[red]julep CLI version unknown[/red]", highlight=True)
            raise Exit(1)

        raise Exit(1)


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
        Option(
            "--no-color",
            help="Disable colored output",
            callback=no_color_callback,
            is_eager=True,
        ),
    ] = not bool(console.color_system),
    quiet: Annotated[
        bool,
        Option(
            "--quiet",
            "-q",
            help="Suppress all output except errors and explicitly requested data",
            callback=quiet_callback,
            is_eager=True,
        ),
    ] = False,
    version: Annotated[
        bool,
        Option(
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
