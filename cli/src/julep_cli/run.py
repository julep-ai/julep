import json
from pathlib import Path
from typing import Annotated
from uuid import UUID

import julep
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

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
            if not isinstance(task_input, dict):
                msg = "Input must be a JSON object (dictionary)"
                raise typer.BadParameter(msg)
        except json.JSONDecodeError as e:
            msg = f"Input must be valid JSON: {e}"
            raise typer.BadParameter(msg)
    elif input_file:
        try:
            with open(input_file) as f:
                task_input = json.load(f)
            if not isinstance(task_input, dict):
                msg = "Input file must contain a JSON object (dictionary)"
                raise typer.BadParameter(msg)
        except FileNotFoundError as e:
            msg = f"Input file not found: {e}"
            raise typer.BadParameter(msg)
        except json.JSONDecodeError as e:
            msg = f"Input file must be valid JSON: {e}"
            raise typer.BadParameter(msg)

    client = get_julep_client()

    # AIDEV-NOTE: Execute task via Julep API and surface errors clearly
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        try:
            run_task = progress.add_task("Creating execution...", start=False)
            progress.start_task(run_task)

            execution = create_execution(client, str(task), task_input)
        except Exception as e:
            error_console.print(
                f"[bold red]Error creating execution: {e}[/bold red]",
                highlight=True,
            )
            raise typer.Exit(1)

    console.print(
        f"Execution created successfully! Execution ID: {execution.id}",
    )

    # AIDEV-NOTE: Execute task via Julep API with specific error handling for different failure types
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        try:
            run_task = progress.add_task("Creating execution...", start=False)
            progress.start_task(run_task)

            execution = create_execution(client, str(task), task_input)
        except julep.NotFoundError as e:
            error_console.print(
                f"[bold red]Task not found: {e}[/bold red]",
                highlight=True,
            )
            raise typer.Exit(1)
        except Exception as e:
            error_console.print(
                f"[bold red]Error creating execution: {e}[/bold red]",
                highlight=True,
            )
            raise typer.Exit(1)

    console.print(
        f"Execution created successfully! Execution ID: {execution.id}",
    )

    if wait:
        logs(execution_id=execution.id, tailing=True)
