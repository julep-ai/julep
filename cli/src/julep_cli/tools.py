import json
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.box import HEAVY_HEAD
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .app import console, error_console, tools_app
from .utils import get_julep_client


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

    client = get_julep_client()

    tool_yaml_contents = yaml.safe_load(Path(definition).read_text())

    if name:
        tool_yaml_contents["name"] = name

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        try:
            create_tool_task = progress.add_task(description="Creating tool", total=None)
            progress.start_task(create_tool_task)
            tool = client.agents.tools.create(agent_id=agent_id, **tool_yaml_contents)
        except Exception as e:
            error_console.print(f"Error creating tool: {e}", highlight=True)
            raise typer.Exit(1)

    console.print(
        Text(f"Tool created successfully. Tool ID: {tool.id}", style="bold green"),
        highlight=True,
    )


@tools_app.command()
def update(
    agent_id: Annotated[
        str,
        typer.Option("--agent-id", "-a", help="ID of the agent the tool is associated with"),
    ],
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

    client = get_julep_client()

    tool_yaml_contents = yaml.safe_load(Path(definition).read_text()) if definition else {}

    if name:
        tool_yaml_contents["name"] = name

    if not tool_yaml_contents:
        error_console.print(
            "Error: No tool name or definition provided", style="bold red", highlight=True
        )
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        try:
            update_tool_task = progress.add_task("Updating tool...", start=False)
            progress.start_task(update_tool_task)

            client.agents.tools.update(agent_id=agent_id, tool_id=tool_id, **tool_yaml_contents)
        except Exception as e:
            error_console.print(f"Error updating tool: {e}", style="bold red", highlight=True)
            raise typer.Exit(1)

    console.print(Text("Tool updated successfully.", style="bold green"), highlight=True)


@tools_app.command()
def delete(
    agent_id: Annotated[
        str,
        typer.Option("--agent-id", "-a", help="ID of the agent the tool is associated with"),
    ],
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

    client = get_julep_client()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        try:
            delete_tool_task = progress.add_task("Deleting tool...", start=False)
            progress.start_task(delete_tool_task)

            client.agents.tools.delete(agent_id=agent_id, tool_id=tool_id)
        except Exception as e:
            error_console.print(f"Error deleting tool: {e}", style="bold red", highlight=True)
            raise typer.Exit(1)

    console.print(Text("Tool deleted successfully.", style="bold green"), highlight=True)


@tools_app.command()
def list(
    agent_id: Annotated[
        str | None, typer.Option("--agent-id", "-a", help="Filter tools by associated agent ID")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output the list in JSON format")
    ] = False,
):
    """List all tools or filter based on criteria.

    Either --agent-id or --task-id must be provided to filter the tools list.
    """
    if not agent_id:
        typer.echo("Error: --agent-id must be provided")
        raise typer.Exit(1)

    client = get_julep_client()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        try:
            list_tools_task = progress.add_task("Listing tools...", start=False)
            progress.start_task(list_tools_task)

            tools = client.agents.tools.list(agent_id=agent_id)
        except Exception as e:
            error_console.print(f"Error listing tools: {e}", style="bold red", highlight=True)
            raise typer.Exit(1)

    if json_output:
        typer.echo(json.dumps(tools, indent=2))
        return

    tools_table = Table(
        title=Text("Available Tools:", style="bold underline magenta"),
        box=HEAVY_HEAD,  # border between cells
        show_lines=True,  # Adds lines between rows
        show_header=True,
        header_style="bold magenta",
        width=130,
    )

    tools_table.add_column("ID", style="green")
    tools_table.add_column("Name", style="cyan")
    tools_table.add_column("Type", style="yellow")
    tools_table.add_column("Description", style="yellow")

    for tool in tools:
        tools_table.add_row(tool.id, tool.name, tool.type, tool.description)

    console.print(tools_table, highlight=True)
