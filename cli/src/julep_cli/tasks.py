import json
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.box import HEAVY_HEAD
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .app import console, error_console, tasks_app
from .utils import DateTimeEncoder, get_julep_client


@tasks_app.command()
def create(
    agent_id: Annotated[
        str,
        typer.Option("--agent-id", "-a", help="ID of the agent the task is associated with"),
    ],
    definition: Annotated[
        str, typer.Option("--definition", "-d", help="Path to the task definition YAML file")
    ],
    name: Annotated[
        str | None,
        typer.Option(
            "--name",
            "-n",
            help="Name of the task (if not provided, uses the definition file name)",
        ),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option(
            "--description",
            help="Description of the task (if not provided, uses the definition file name)",
        ),
    ] = None,
    metadata: Annotated[
        str | None, typer.Option("--metadata", help="JSON metadata for the task")
    ] = None,
    inherit_tools: Annotated[
        bool, typer.Option("--inherit-tools", help="Inherit tools from the associated agent")
    ] = False,
):
    """Create a new task for an agent.

    If other options are provided alongside the definition file, they will override values in the definition.
    """
    try:
        metadata_dict = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError as e:
        error_console.print(f"Error parsing JSON: {e}", style="bold red", highlight=True)
        raise typer.Exit(1)

    client = get_julep_client()

    task_yaml_contents = yaml.safe_load(Path(definition).read_text())

    # Override values from the definition file with the provided options
    if name:
        task_yaml_contents["name"] = name
    if description:
        task_yaml_contents["description"] = description
    if metadata:
        task_yaml_contents["metadata"] = metadata_dict
    if inherit_tools is True:
        task_yaml_contents["inherit_tools"] = True
    elif inherit_tools is False:
        task_yaml_contents["inherit_tools"] = False

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        try:
            create_task_task = progress.add_task("Creating task...", start=False)
            progress.start_task(create_task_task)

            task = client.tasks.create(
                agent_id=agent_id,
                **task_yaml_contents,
            )

        except Exception as e:
            error_console.print(f"Error creating task: {e}", style="bold red", highlight=True)
            raise typer.Exit(1)

    console.print(Text(f"Task created successfully. Task ID: {task.id}", style="bold green"))


@tasks_app.command()
def update(
    agent_id: Annotated[
        str,
        typer.Option("--agent-id", "-a", help="ID of the agent the task is associated with"),
    ],
    task_id: Annotated[str, typer.Option("--id", help="ID of the task to update")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="New name for the task")
    ] = None,
    description: Annotated[
        str | None, typer.Option("--description", help="New description for the task")
    ] = None,
    definition: Annotated[
        str | None,
        typer.Option(
            "--definition", "-d", help="Path to the updated task definition YAML file"
        ),
    ] = None,
    metadata: Annotated[
        str | None, typer.Option("--metadata", help="JSON metadata for the task")
    ] = None,
    inherit_tools: Annotated[
        bool | None,
        typer.Option("--inherit-tools", help="Inherit tools from the associated agent"),
    ] = None,
):
    """Update an existing task's details"""
    try:
        metadata_dict = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError as e:
        error_console.print(f"Error parsing JSON: {e}", style="bold red", highlight=True)
        raise typer.Exit(1)

    task_yaml_contents = yaml.safe_load(Path(definition).read_text())

    if name:
        task_yaml_contents["name"] = name
    if description:
        task_yaml_contents["description"] = description
    if metadata:
        task_yaml_contents["metadata"] = metadata_dict
    if inherit_tools is True:
        task_yaml_contents["inherit_tools"] = True
    elif inherit_tools is False:
        task_yaml_contents["inherit_tools"] = False

    client = get_julep_client()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        try:
            update_task_task = progress.add_task("Updating task...", start=False)
            progress.start_task(update_task_task)

            client.tasks.create_or_update(
                agent_id=agent_id, task_id=task_id, **task_yaml_contents
            )
        except Exception as e:
            error_console.print(f"Error updating task: {e}", style="bold red", highlight=True)
            raise typer.Exit(1)

    console.print(Text("Task updated successfully.", style="bold green"), highlight=True)


@tasks_app.command()
def list(
    agent_id: Annotated[
        str | None, typer.Option("--agent-id", "-a", help="Filter tasks by associated agent ID")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output the list in JSON format")
    ] = False,
):
    """List all tasks or filter based on criteria"""
    client = get_julep_client()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        try:
            list_tasks_task = progress.add_task(description="Fetching tasks", total=None)
            progress.start_task(list_tasks_task)

            tasks = client.tasks.list(agent_id=agent_id).items
        except Exception as e:
            error_console.print(Text(f"Error fetching tasks: {e}", style="bold red"))
            raise typer.Exit(1)

    if json_output:
        console.print(
            json.dumps([task.model_dump() for task in tasks], indent=2, cls=DateTimeEncoder),
            highlight=True,
        )
        return

    # Table format output
    tasks_table = Table(
        title=Text("Available Tasks:", style="bold underline magenta"),
        box=HEAVY_HEAD,  # border between cells
        show_lines=True,  # Adds lines between rows
        show_header=True,
        header_style="bold magenta",
        width=150,
    )
    tasks_table.add_column("Name", style="cyan", width=40)
    tasks_table.add_column("Description", style="yellow", width=50)
    tasks_table.add_column("ID", style="green", width=40)

    for task in tasks:
        tasks_table.add_row(task.name, task.description, task.id)

    console.print(tasks_table, highlight=True)
