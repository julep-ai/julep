from pathlib import Path
from typing import Annotated

import typer
import yaml

from .app import app
from .models import LockFileContents
from .utils import get_lock_file


@app.command()
def ls(
    source: Annotated[
        Path,
        typer.Option(
            "--source",
            "-s",
            help="Path to list",
        ),
    ] = Path.cwd(),
):
    """
    List synced entities in a julep source project.
    """

    lock_file: LockFileContents = get_lock_file(source)

    if lock_file.agents:
        typer.echo("Agents:\n")
        for agent in lock_file.agents:

            # Read the agent yaml file
            agent_yaml_contents = yaml.safe_load(Path(source / agent.path).read_text())

            # Add the id to the agent content
            agent_yaml_contents["id"] = agent.id

            # Print the agent content
            for key, value in agent_yaml_contents.items():
                typer.echo(f"{key}: {value}")

            typer.echo(f"definition file: {agent.path}")

            typer.echo("------------")

    if lock_file.tasks:
        typer.echo("Tasks:\n")
        for task in lock_file.tasks:
            task_yaml_contents = yaml.safe_load(Path(source / task.path).read_text())

            typer.echo(f"name: {task_yaml_contents.get('name')}")
            typer.echo(f"id: {task.id}")
            typer.echo(f"definition file: {task.path}")
            typer.echo("------------")

    if lock_file.tools:
        typer.echo("Tools:\n")
        for tool in lock_file.tools:
            tool_yaml_contents = yaml.safe_load(Path(source / tool.path).read_text())

            typer.echo(f"name: {tool_yaml_contents.get('name')}")
            typer.echo(f"id: {tool.id}")
            typer.echo(f"definition file: {tool.path}")
