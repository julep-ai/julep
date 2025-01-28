import json
from typing import Annotated

import typer

from .app import agents_app


@agents_app.command()
def create(
    name: Annotated[str | None, typer.Option("--name", "-n", help="Name of the agent")] = None,
    model: Annotated[
        str | None, typer.Option("--model", "-m", help="Model to be used by the agent")
    ] = None,
    about: Annotated[
        str | None, typer.Option("--about", "-a", help="Description of the agent")
    ] = None,
    default_settings: Annotated[
        str | None,
        typer.Option("--default-settings", help="Default settings for the agent (JSON string)"),
    ] = None,
    metadata: Annotated[
        str | None, typer.Option("--metadata", help="Metadata for the agent (JSON string)")
    ] = None,
    instructions: Annotated[
        list[str],
        typer.Option(
            "--instructions", help="Instructions for the agent, can be specified multiple times"
        ),
    ] = [],
    definition: Annotated[
        str | None, typer.Option("--definition", "-d", help="Path to an agent definition file")
    ] = None,
):
    """Create a new AI agent. Either provide a definition file or use the other options."""
    # Validate that either definition is provided or name/model
    if not definition and not (name and model):
        typer.echo("Error: Must provide either a definition file or name and model", err=True)
        raise typer.Exit(1)

    try:
        json.loads(metadata) if metadata else {}
        json.loads(default_settings) if default_settings else {}
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {e}", err=True)
        raise typer.Exit(1)

    # TODO: Implement actual API call
    if definition:
        typer.echo(f"Created agent from definition file '{definition}'")
    else:
        typer.echo(f"Created agent '{name}' with model '{model}'")


@agents_app.command()
def update(
    id: Annotated[str, typer.Option("--id", help="ID of the agent to update")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="New name for the agent")
    ] = None,
    model: Annotated[
        str | None, typer.Option("--model", "-m", help="New model for the agent")
    ] = None,
    about: Annotated[
        str | None, typer.Option("--about", "-a", help="New description for the agent")
    ] = None,
    metadata: Annotated[
        str | None, typer.Option("--metadata", help="Metadata for the agent (JSON string)")
    ] = None,
    default_settings: Annotated[
        str | None,
        typer.Option("--default-settings", help="Default settings for the agent (JSON string)"),
    ] = None,
    instructions: Annotated[
        list[str],
        typer.Option(
            "--instructions", help="Instructions for the agent, can be specified multiple times"
        ),
    ] = [],
):
    """Update an existing AI agent's details"""
    try:
        metadata_dict = json.loads(metadata) if metadata else {}
        settings_dict = json.loads(default_settings) if default_settings else {}
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {e}", err=True)
        raise typer.Exit(1)

    updates = {
        k: v
        for k, v in {
            "name": name,
            "model": model,
            "about": about,
            "metadata": metadata_dict if metadata else None,
            "default_settings": settings_dict if default_settings else None,
            "instructions": instructions if instructions else None,
        }.items()
        if v is not None
    }

    if not updates:
        typer.echo("No updates provided", err=True)
        raise typer.Exit(1)

    # TODO: Implement actual API call
    typer.echo(f"Updated agent '{id}'")


@agents_app.command()
def delete(
    id: Annotated[str, typer.Option("--id", help="ID of the agent to delete")],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force deletion without confirmation",
        ),
    ] = False,
):
    """Delete an existing AI agent"""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete agent '{id}'?")
        if not confirm:
            typer.echo("Operation cancelled")
            raise typer.Exit

    # TODO: Implement actual API call
    typer.echo(f"Deleted agent '{id}'")


@agents_app.command()
def list(
    metadata_filter: Annotated[
        str | None,
        typer.Option(
            "--metadata-filter", help="Filter agents based on metadata criteria (JSON string)"
        ),
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output the list in JSON format")
    ] = False,
):
    """List all AI agents or filter based on metadata"""
    try:
        json.loads(metadata_filter) if metadata_filter else {}
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing metadata filter JSON: {e}", err=True)
        raise typer.Exit(1)

    # TODO: Implement actual API call
    # Mock data for demonstration
    agents = [
        {"id": "agent1", "name": "Test Agent 1", "model": "gpt-4"},
        {"id": "agent2", "name": "Test Agent 2", "model": "claude-3"},
    ]

    if json_output:
        typer.echo(json.dumps(agents, indent=2))
        return

    # Table format output
    typer.echo("Available agents:")
    typer.echo("ID\tName\tModel")
    typer.echo("-" * 40)
    for agent in agents:
        typer.echo(f"{agent['id']}\t{agent['name']}\t{agent['model']}")


@agents_app.command()
def get(
    id: Annotated[str, typer.Option("--id", help="ID of the agent to retrieve")],
    json_output: Annotated[bool, typer.Option("--json", help="Output in JSON format")] = False,
):
    """Get an agent by its ID"""
    # TODO: Implement actual API call
    # Mock data for demonstration
    agent = {
        "id": id,
        "name": "Test Agent",
        "model": "gpt-4",
        "about": "A test agent",
        "created_at": "2024-03-14T12:00:00Z",
    }

    if json_output:
        typer.echo(json.dumps(agent, indent=2))
        return

    # Pretty print output
    typer.echo("Agent details:")
    for key, value in agent.items():
        typer.echo(f"{key}: {value}")
