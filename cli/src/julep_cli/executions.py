import json
from typing import Annotated

import typer
from julep import Client, Julep
from rich.progress import Progress, SpinnerColumn, TextColumn

from .app import console, error_console, executions_app
from .utils import get_julep_client, persist_attribute


@persist_attribute("execution_id", extractor=lambda exec_obj: exec_obj.id)
def create_execution(client: Julep | Client, task_id: str, input_data: dict):
    """
    Create an execution and persist its execution ID to the state database.
    """
    return client.executions.create(task_id=task_id, input=input_data)


@executions_app.command()
def create(
    task_id: Annotated[str, typer.Option("--task-id", help="ID of the task to execute")],
    input: Annotated[str, typer.Option("--input", help="Input for the execution")],
):
    """
    Create a new execution.
    """

    client = get_julep_client()

    try:
        input_data = json.loads(input)
    except json.JSONDecodeError as e:
        error_console.print(f"[bold red]Invalid JSON input: {e}[/bold red]", highlight=True)
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Creating execution...", start=False)
        progress.start_task(task)

        try:
            execution = create_execution(client, task_id, input_data)
        except Exception as e:
            error_console.print(f"[bold red]Error creating execution: {e}[/bold red]")
            raise typer.Exit(1)

    console.print(
        f"[bold blue]Execution created successfully![/bold blue]\n[green]Execution ID: {execution.id}[/green]"
    )
