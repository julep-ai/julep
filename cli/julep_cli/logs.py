import json
import time
from typing import Annotated
from julep.resources.executions.transitions import Transition

import typer

from .app import app, console, error_console
from .utils import get_julep_client
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.box import HEAVY

@app.command()
def logs(
    execution_id: Annotated[str, typer.Option("--execution-id", "-e", help="ID of the execution to log")],
    tailing: Annotated[bool, typer.Option("--tail", "-t", help="Whether to tail the logs")] = False,
):
    """
    Log the output of an execution.
    """

    transitions_table = Table(
        title="Execution Transitions",
        box=HEAVY, # border between cells
        show_lines=True,  # Adds lines between rows
        show_header=True,
        header_style="bold magenta",
    )

    transitions_table.add_column(
        "Transition Type",
        style="bold cyan",
        no_wrap=True,
        justify="center",
        vertical="middle",
    )
    transitions_table.add_column(
        "Transition Output",
        style="green",
    )

    def display_transitions(transitions: list[Transition]):
        for transition in reversed(transitions):
            transitions_table.add_row(transition.type, json.dumps(
                transition.output, indent=4))

        console.print(transitions_table)


    client = get_julep_client()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        try:
            fetch_transitions = progress.add_task(description="Fetching transitions", total=None)
            progress.start_task(fetch_transitions)

            transitions = client.executions.transitions.list(execution_id=execution_id).items
        except Exception as e:
            error_console.print(Text(f"Error fetching transitions: {e}", style="bold red"))
            raise typer.Exit(1)
        finally:
            progress.remove_task(fetch_transitions)
            display_transitions(transitions)

    if tailing:
        while True:
            fetched_transitions = client.executions.transitions.list(execution_id=execution_id).items
            new_transitions = fetched_transitions[:len(fetched_transitions) - len(transitions)]

            if new_transitions:
                # FIXME: This prints the table multiple times
                display_transitions(new_transitions)

            transitions = fetched_transitions


            if transitions and transitions[0].type in ["finish", "cancelled", "error"]:
                break

            time.sleep(1)
