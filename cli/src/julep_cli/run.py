import json
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer

from .app import app, console, error_console
from .executions import create_execution
from .logs import logs
from .utils import get_julep_client


@app.command()
def run(
    task: Annotated[
        UUID,
        typer.Option(
            "--task",
            "-t",
            help="ID of the task to execute",
        ),
    ],
    input: Annotated[
        str | None,
        typer.Option(
            "--input",
            help="JSON string representing the input for the task (defaults to {})",
        ),
    ] = None,
    input_file: Annotated[
        Path | None,
        typer.Option(
            "--input-file",
            help="Path to a file containing the input for the task",
        ),
    ] = None,
    wait: Annotated[
        bool,
        typer.Option(
            "--wait",
            help="Wait for the task to complete before exiting, stream logs to stdout",
        ),
    ] = False,
):
    """Run a defined task with specified input parameters"""

    # Parse input
    task_input = {}
    if input and input_file:
        msg = "Cannot specify both --input and --input-file"
        raise typer.BadParameter(msg)

    if input:
        try:
            task_input = json.loads(input)
        except json.JSONDecodeError:
            msg = "Input must be valid JSON"
            raise typer.BadParameter(msg)
    elif input_file:
        try:
            with open(input_file) as f:
                task_input = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            msg = f"Error reading input file: {e}"
            raise typer.BadParameter(msg)

    # TODO: Implement task execution logic
    typer.echo(f"Running task '{task}' with input: {task_input}")

    client = get_julep_client()

    try:
        execution = create_execution(client, str(task), task_input)
        console.print(f"Execution created successfully! Execution ID: {execution.id}")
    except Exception as e:
        error_console.print(f"Error creating execution: {e}", highlight=True)
        raise typer.Exit(1)

    if wait:
        logs(execution_id=execution.id, tailing=True)
