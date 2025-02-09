import json
from typing import Annotated

import typer
from rich.box import HEAVY_HEAD
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .app import agents_app, console, error_console
from .utils import DateTimeEncoder, get_julep_client

SINGLE_AGENT_TABLE_WIDTH = 100
SINGLE_AGENT_COLUMN_WIDTH = 50


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

    if definition:
        # TODO: implement definition file parsing
        error_console.print("Passing definition file is not implemented yet", highlight=True)
        raise typer.Exit(1)

    # Validate that either definition is provided or name/model
    if not definition and not (name and model):
        error_console.print(
            "Error: Must provide either a definition file or name and model", highlight=True
        )
        raise typer.Exit(1)

    try:
        if metadata:
            json.loads(metadata)
        if default_settings:
            json.loads(default_settings)
    except json.JSONDecodeError as e:
        error_console.print(f"Error parsing JSON: {e}", highlight=True)
        raise typer.Exit(1)

    client = get_julep_client()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        try:
            create_agent_task = progress.add_task("Creating agent...", start=False)
            progress.start_task(create_agent_task)

            agent = client.agents.create(
                name=name,
                model=model,
                about=about,
                default_settings=default_settings,
                metadata=metadata,
                instructions=instructions,
            )

        except Exception as e:
            error_console.print(f"Error creating agent: {e}", style="bold red", highlight=True)
            raise typer.Exit(1)

    console.print(Text(f"Agent created successfully. Agent ID: {agent.id}", style="bold green"))


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
        error_console.print(f"Error parsing JSON: {e}", highlight=True)
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
        error_console.print("No updates provided", highlight=True)
        raise typer.Exit(1)

    client = get_julep_client()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        try:
            update_agent_task = progress.add_task("Updating agent...", start=False)
            progress.start_task(update_agent_task)

            client.agents.update(agent_id=id, **updates)
        except Exception as e:
            error_console.print(f"Error updating agent: {e}", highlight=True)
            raise typer.Exit(1)

    console.print(Text("Agent updated successfully.", style="bold green"), highlight=True)


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
            error_console.print("Operation cancelled", highlight=True)
            raise typer.Exit(1)

    client = get_julep_client()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        try:
            delete_agent_task = progress.add_task("Deleting agent...", start=False)
            progress.start_task(delete_agent_task)

            client.agents.delete(id)
        except Exception as e:
            error_console.print(f"Error deleting agent: {e}", highlight=True)
            raise typer.Exit(1)

    console.print(Text("Agent deleted successfully.", style="bold green", highlight=True))


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
        typer.echo(f"Error parsing metadata filter JSON: {e}")
        raise typer.Exit(1)

    client = get_julep_client()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        try:
            list_agents_task = progress.add_task(description="Fetching agents", total=None)
            progress.start_task(list_agents_task)

            agents = client.agents.list(metadata_filter=metadata_filter).items
        except Exception as e:
            error_console.print(
                Text(f"Error fetching agents: {e}", style="bold red", highlight=True)
            )
            raise typer.Exit(1)

    if json_output:
        typer.echo([agent.model_dump_json(indent=2) for agent in agents])
        return

    # Table format output
    agent_table = Table(
        title=Text("Available Agents:", style="bold underline magenta"),
        box=HEAVY_HEAD,  # border between cells
        show_lines=True,  # Adds lines between rows
        show_header=True,
        header_style="bold magenta",
        width=140,
    )
    agent_table.add_column("Name", style="cyan", width=25)
    agent_table.add_column("About", style="cyan", width=50)
    agent_table.add_column("Model", style="yellow", width=25)
    agent_table.add_column("ID", style="green", width=40)

    for agent in agents:
        agent_table.add_row(agent.name, agent.about, agent.model, agent.id)

    console.print(agent_table, highlight=True)


@agents_app.command()
def get(
    id: Annotated[str, typer.Option("--id", help="ID of the agent to retrieve")],
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output in JSON format",
            is_flag=True,
            show_default=True,
        ),
    ] = False,
):
    """Get an agent by its ID"""
    client = get_julep_client()

    agent = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        try:
            get_agent_task = progress.add_task("Retrieving agent...", start=False)
            progress.start_task(get_agent_task)

            agent = client.agents.get(id)
        except Exception as e:
            error_console.print(f"Error retrieving agent: {e}", highlight=True)
            raise typer.Exit(1)

    console.print(Text("Agent retrieved successfully.", style="bold green"), highlight=True)

    if json_output:
        console.print(
            json.dumps(agent.model_dump(), indent=2, cls=DateTimeEncoder), highlight=True
        )
        return

    # Create a table for agent details
    agent_table = Table(
        title=Text("Agent Details:", style="bold underline magenta"),
        header_style="bold magenta",
        width=SINGLE_AGENT_TABLE_WIDTH,
    )
    agent_table.add_column("Key", style="green", width=SINGLE_AGENT_COLUMN_WIDTH)
    agent_table.add_column("Value", style="cyan", width=SINGLE_AGENT_COLUMN_WIDTH * 2)

    for key, value in agent.model_dump().items():
        agent_table.add_row(key, str(value))

    console.print(agent_table, highlight=True)
