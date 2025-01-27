import json
from typing import Annotated

import typer

from .app import tools_app


@tools_app.command()
def create(
    agent_id: Annotated[
        str,
        typer.Option("--agent-id", "-a", help="ID of the agent the tool is associated with"),
    ],
    definition: Annotated[
        str, typer.Option("--definition", "-d", help="Path to the tool configuration YAML file")
    ],
    name: Annotated[
        str | None,
        typer.Option(
            "--name",
            "-n",
            help="Name of the tool (if not provided, uses filename from definition)",
        ),
    ] = None,
):
    """Create a new tool for an agent.

    Requires either a definition file or direct parameters. If both are provided,
    command-line options override values from the definition file.
    """
    # TODO: Implement actual API call
    typer.echo(f"Created tool '{name}' for agent '{agent_id}'")


@tools_app.command()
def update(
    tool_id: Annotated[str, typer.Option("--id", help="ID of the tool to update")],
    definition: Annotated[
        str | None,
        typer.Option(
            "--definition", "-d", help="Path to the updated tool configuration YAML file"
        ),
    ] = None,
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="New name for the tool")
    ] = None,
):
    """Update an existing tool's details.

    Updates can be made using either a definition file or direct parameters.
    If both are provided, command-line options override values from the definition file.
    """
    # TODO: Implement actual API call
    typer.echo(f"Updated tool '{tool_id}'")


@tools_app.command()
def delete(
    tool_id: Annotated[str, typer.Option("--id", help="ID of the tool to delete")],
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", help="Force the deletion without prompting for confirmation"
        ),
    ] = False,
):
    """Delete an existing tool.

    By default, prompts for confirmation unless --force is specified.
    """
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete tool '{tool_id}'?")
        if not confirm:
            typer.echo("Operation cancelled")
            return

    # TODO: Implement actual API call
    typer.echo(f"Deleted tool '{tool_id}'")


@tools_app.command()
def list(
    agent_id: Annotated[
        str | None, typer.Option("--agent-id", "-a", help="Filter tools by associated agent ID")
    ] = None,
    task_id: Annotated[
        str | None, typer.Option("--task-id", "-t", help="Filter tools by associated task ID")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output the list in JSON format")
    ] = False,
):
    """List all tools or filter based on criteria.

    Either --agent-id or --task-id must be provided to filter the tools list.
    """
    if not agent_id and not task_id:
        typer.echo("Error: Either --agent-id or --task-id must be provided", err=True)
        raise typer.Exit(1)

    # TODO: Implement actual API call
    # Mock data for demonstration
    tools = [
        {"id": "tool1", "name": "Web Search", "agent_id": "agent1"},
        {"id": "tool2", "name": "API Call", "agent_id": "agent2"},
    ]

    if json_output:
        typer.echo(json.dumps(tools, indent=2))
        return

    # Table format output
    typer.echo("Available tools:")
    typer.echo("ID\tName\tAgent ID")
    typer.echo("-" * 40)
    for tool in tools:
        typer.echo(f"{tool['id']}\t{tool['name']}\t{tool['agent_id']}")
