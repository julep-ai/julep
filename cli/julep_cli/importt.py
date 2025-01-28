import datetime
import hashlib
from pathlib import Path

import typer
from julep.types.agent import Agent

from .app import import_app
from .models import LockedEntity
from .utils import (
    add_entity_to_lock_file,
    get_entity_from_lock_file,
    get_julep_client,
    update_existing_entity_in_lock_file,
    update_yaml_for_existing_entity,
)


@import_app.command()
def agent(
    id: str = typer.Option(..., "--id", "-i", help="ID of the agent to import"),
    output: Path = typer.Option(
        Path.cwd() / "src/agents",
        "--output",
        "-o",
        help="Path to save the imported agent. Defaults to cwd/src/agents",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Import an agent from the Julep platform.
    """

    client = get_julep_client()

    # Importing an existing agent
    if locked_agent := get_entity_from_lock_file(type="agent", id=id):
        typer.echo(f"Agent '{id}' already exists in the lock file")
        confirm = typer.confirm(
            f"Do you want to overwrite the existing agent in the lock file and {locked_agent.get('path')}?"
        )

        # User cancelled the operation (doesn't want to overwrite the existing agent)
        if not confirm:
            typer.echo("Operation cancelled")
            raise typer.Exit(1)

        # User wants to overwrite the existing agent
        typer.echo("Overwriting existing agent...")

        # Fetch the agent from the remote
        typer.echo(f"Fetching agent '{id}' from remote...")
        remote_agent: Agent = client.agents.get(agent_id=id)

        # TODO: Decide where to store (specified --output or current path specified in lock file)
        agent_yaml_path = locked_agent.get("path")

        typer.echo(f"Updating agent '{id}' in '{agent_yaml_path}'...")
        update_yaml_for_existing_entity(agent_yaml_path, remote_agent.model_dump())

        typer.echo(f"Updating agent '{id}' in lock file...")
        update_existing_entity_in_lock_file(
            type="agent",
            new_entity={
                "path": agent_yaml_path,
                "id": id,
                "last_synced": datetime.datetime.now().isoformat(timespec="milliseconds") + "Z",
                "revision_hash": hashlib.sha256(
                    remote_agent.model_dump_json().encode()
                ).hexdigest(),
            },
        )

        typer.echo(f"Agent '{id}' imported successfully to '{agent_yaml_path}'")

        return

    # Importing a new agent (doesn't exist in lock file)
    if not yes:
        confirm = typer.confirm(f"Are you sure you want to import agent '{id}' to '{output}'?")
        if not confirm:
            typer.echo("Operation cancelled")
            raise typer.Exit

    try:
        client = get_julep_client()
        agent_data = client.agents.get(agent_id=id)

        # Convert to lowercase and replace spaces with underscores
        agent_name = agent_data.name.lower().replace(" ", "_")

        agent_yaml_path = output / f"{agent_name}.yaml"
        typer.echo(f"Adding agent '{agent_data.name}' to '{agent_yaml_path}'...")
        update_yaml_for_existing_entity(agent_yaml_path, agent_data.model_dump())

        typer.echo(f"Agent '{id}' imported successfully to '{agent_yaml_path}'")

        typer.echo(f"Adding agent '{id}' to lock file...")
        add_entity_to_lock_file(
            type="agent",
            new_entity=LockedEntity(
                path=str(agent_yaml_path),
                id=agent_data.id,
                last_synced=datetime.datetime.now().isoformat(timespec="milliseconds") + "Z",
                revision_hash=hashlib.sha256(
                    agent_data.model_dump_json().encode()
                ).hexdigest(),
            ),
        )

    except Exception as e:
        typer.echo(f"Error importing agent: {e}", err=True)
        raise typer.Exit(1)
