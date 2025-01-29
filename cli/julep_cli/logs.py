import json
import time
from typing import Annotated

import typer

from .app import app
from .utils import get_julep_client


@app.command()
def logs(
    execution_id: Annotated[str, typer.Option("--execution-id", "-e", help="ID of the execution to log")],
    tailing: Annotated[bool, typer.Option("--tail", "-t", help="Whether to tail the logs")] = False,
):
    """
    Log the output of an execution.
    """

    client = get_julep_client()

    transitions = client.executions.transitions.list(execution_id=execution_id).items
    for transition in reversed(transitions):
        typer.echo(f"Transition Type: {transition.type}")
        typer.echo("Transition Output:")
        typer.echo(json.dumps(transition.output, indent=4))
        typer.echo("--------------------------------")

    if tailing:
        while True:
            fetched_transitions = client.executions.transitions.list(execution_id=execution_id).items
            new_transitions = fetched_transitions[:len(fetched_transitions) - len(transitions)]

            for transition in reversed(new_transitions):
                typer.echo(f"Transition Type: {transition.type}")
                typer.echo("Transition Output:")
                typer.echo(json.dumps(transition.output, indent=4))
                typer.echo("--------------------------------")

            transitions = fetched_transitions

            if transitions[0].type in ["finish", "cancelled", "error"]:
                break

            time.sleep(1)
