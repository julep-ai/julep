import json
from typing import Annotated

import typer

from .app import tools_app


@tools_app.command()
def create(
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the tool")],
    tool_type: Annotated[
        str,
        typer.Option(
            "--type", "-t", help="Type of the tool (integration, api_call, function, system)"
        ),
    ],
    agent_id: Annotated[
        str,
        typer.Option("--agent-id", "-a", help="ID of the agent the tool is associated with"),
    ],
    config: Annotated[
        str, typer.Option("--config", "-c", help="Path to the tool configuration YAML file")
    ],
):
    """Create a new tool for an agent"""
    # TODO: Implement actual API call
    typer.echo(f"Created tool '{name}' of type '{tool_type}' for agent '{agent_id}'")


@tools_app.command()
def update(
    tool_id: Annotated[str, typer.Option("--id", help="ID of the tool to update")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New name for the tool")] = None,
    config: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Path to the updated tool configuration YAML file"),
    ] = None,
):
    """Update an existing tool"""
    # TODO: Implement actual API call
    typer.echo(f"Updated tool '{tool_id}'")


@tools_app.command()
def delete(
    tool_id: Annotated[str, typer.Option("--id", help="ID of the tool to delete")],
):
    """Delete an existing tool"""
    # TODO: Implement actual API call
    typer.echo(f"Deleted tool '{tool_id}'")


@tools_app.command()
def list(
    agent_id: Annotated[
        str | None, typer.Option("--agent-id", "-a", help="Filter tools by associated agent ID")
    ] = None,
    tool_type: Annotated[str | None, typer.Option("--type", "-t", help="Filter tools by type")] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output the list in JSON format")
    ] = False,
):
    """List all tools or filter based on criteria"""
    # TODO: Implement actual API call
    # Mock data for demonstration
    tools = [
        {"id": "tool1", "name": "Web Search", "type": "integration", "agent_id": "agent1"},
        {"id": "tool2", "name": "API Call", "type": "api_call", "agent_id": "agent2"},
    ]

    if json_output:
        typer.echo(json.dumps(tools, indent=2))
        return

    # Table format output
    typer.echo("Available tools:")
    typer.echo("ID\tName\tType\tAgent ID")
    typer.echo("-" * 50)
    for tool in tools:
        typer.echo(f"{tool['id']}\t{tool['name']}\t{tool['type']}\t{tool['agent_id']}")
