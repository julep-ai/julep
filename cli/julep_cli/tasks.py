import json
from typing import Annotated

import typer

from .app import tasks_app


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
        json.loads(metadata) if metadata else {}
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {e}", err=True)
        raise typer.Exit(1)

    # TODO: Implement actual API call
    typer.echo(f"Created task '{name}' for agent '{agent_id}'")


@tasks_app.command()
def update(
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
        json.loads(metadata) if metadata else {}
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {e}", err=True)
        raise typer.Exit(1)

    # TODO: Implement actual API call
    typer.echo(f"Updated task '{task_id}'")


@tasks_app.command()
def delete(
    task_id: Annotated[str, typer.Option("--id", help="ID of the task to delete")],
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Force deletion without confirmation prompt")
    ] = False,
):
    """Delete an existing task"""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete task '{task_id}'?")
        if not confirm:
            raise typer.Abort

    # TODO: Implement actual API call
    typer.echo(f"Deleted task '{task_id}'")


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
    # TODO: Implement actual API call
    # Mock data for demonstration
    tasks = [
        {"id": "task1", "name": "Test Task 1", "agent_id": "agent1"},
        {"id": "task2", "name": "Test Task 2", "agent_id": "agent2"},
    ]

    if json_output:
        typer.echo(json.dumps(tasks, indent=2))
        return

    # Table format output
    typer.echo("Available tasks:")
    typer.echo("ID\tName\tAgent ID")
    typer.echo("-" * 40)
    for task in tasks:
        typer.echo(f"{task['id']}\t{task['name']}\t{task['agent_id']}")
