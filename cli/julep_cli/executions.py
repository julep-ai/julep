import json
from typing import Annotated

import typer

from .app import executions_app
from .utils import get_julep_client


@executions_app.command()
def create(
    task_id: Annotated[str, typer.Option("--task-id", help="ID of the task to execute")],
    input: Annotated[str, typer.Option("--input", help="Input for the execution")],
):
    """
    Create a new execution.
    """

    client = get_julep_client()

    input = json.loads(input)

    typer.echo(f"type of input: {type(input)}")

    try:
        execution = client.executions.create(task_id=task_id, input=input)
    except Exception as e:
        typer.echo(f"Error creating execution: {e}")
        raise typer.Exit(1)

    typer.echo(f"Execution created with ID: {execution.id}")
