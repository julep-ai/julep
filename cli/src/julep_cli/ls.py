from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.table import Table
from rich.text import Text

from .app import app, console
from .models import LockFileContents
from .utils import get_lock_file

MIN_TABLE_WIDTH = 200


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
        agents_table = Table(
            title=Text("Agents:", style="bold underline magenta"),
            header_style="bold magenta",
            min_width=MIN_TABLE_WIDTH,
        )
        agents_table.add_column("Name", style="green")
        agents_table.add_column("About", style="green")
        agents_table.add_column("Model", style="green")
        agents_table.add_column("Definition File", style="yellow")
        agents_table.add_column("ID", style="cyan", no_wrap=True)

        for agent in lock_file.agents:
            agent_yaml_contents: dict = yaml.safe_load(Path(source / agent.path).read_text())
            agent_yaml_contents["id"] = agent.id
            agents_table.add_row(
                agent_yaml_contents.get("name", "N/A"),
                agent_yaml_contents.get("about", "N/A"),
                agent_yaml_contents.get("model", "N/A"),
                str(agent.path),
                str(agent_yaml_contents["id"]),
            )

        console.print(agents_table, highlight=True)

    if lock_file.tasks:
        tasks_table = Table(
            title=Text("Tasks:", style="bold underline magenta"),
            header_style="bold magenta",
            min_width=MIN_TABLE_WIDTH,
        )
        tasks_table.add_column("Name", style="green")
        tasks_table.add_column("Description", style="green")
        tasks_table.add_column("Definition File", style="yellow")
        tasks_table.add_column("ID", style="cyan", no_wrap=True)

        for task in lock_file.tasks:
            task_yaml_contents: dict = yaml.safe_load(Path(source / task.path).read_text())
            tasks_table.add_row(
                task_yaml_contents.get("name", "N/A"),
                task_yaml_contents.get("description", "N/A"),
                str(task.path),
                str(task.id),
            )

        console.print(tasks_table, highlight=True)

    if lock_file.tools:
        tools_table = Table(
            title=Text("Tools:", style="bold underline magenta"),
            header_style="bold magenta",
            min_width=MIN_TABLE_WIDTH,
        )

        tools_table.add_column("Name", style="green")
        tools_table.add_column("Description", style="green")
        tools_table.add_column("Definition File", style="yellow")
        tools_table.add_column("ID", style="cyan", no_wrap=True)

        for tool in lock_file.tools:
            tool_yaml_contents: dict = yaml.safe_load(Path(source / tool.path).read_text())
            tools_table.add_row(
                tool_yaml_contents.get("name", "N/A"),
                tool_yaml_contents.get("description", "N/A"),
                str(tool.path),
                str(tool.id),
            )

        console.print(tools_table, highlight=True)
