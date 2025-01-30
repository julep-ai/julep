from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.table import Table
from rich.text import Text

from .app import app, console
from .models import LockFileContents
from .utils import get_lock_file

TABLE_WIDTH = 150
COLUMN_WIDTH = TABLE_WIDTH // 3


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
            width=TABLE_WIDTH
        )
        agents_table.add_column("Name", style="green", width=COLUMN_WIDTH)
        agents_table.add_column("Definition File", style="yellow", width=COLUMN_WIDTH)
        agents_table.add_column("ID", style="cyan", no_wrap=True, width=COLUMN_WIDTH)

        for agent in lock_file.agents:
            agent_yaml_contents = yaml.safe_load(
                Path(source / agent.path).read_text())
            agent_yaml_contents["id"] = agent.id
            agents_table.add_row(
                agent_yaml_contents.get("name", "N/A"),
                str(agent_yaml_contents["id"]),
                str(agent.path),
            )

        console.print(agents_table)

    if lock_file.tasks:
        tasks_table = Table(
            title=Text("Tasks:", style="bold underline magenta"),
            header_style="bold magenta",
            width=TABLE_WIDTH
        )
        tasks_table.add_column("Name", style="green", width=COLUMN_WIDTH)
        tasks_table.add_column("Definition File", style="yellow", width=COLUMN_WIDTH)
        tasks_table.add_column("ID", style="cyan", no_wrap=True, width=COLUMN_WIDTH)

        for task in lock_file.tasks:
            task_yaml_contents = yaml.safe_load(
                Path(source / task.path).read_text())
            tasks_table.add_row(
                task_yaml_contents.get("name", "N/A"),
                str(task.path),
                str(task.id),
            )

        console.print(tasks_table)

    if lock_file.tools:
        tools_table = Table(
            title=Text("Tools:", style="bold underline magenta"),
            header_style="bold magenta",
            width=150
        )
        tools_table.add_column("Name", style="green", width=COLUMN_WIDTH)
        tools_table.add_column("Definition File", style="yellow", width=COLUMN_WIDTH)
        tools_table.add_column("ID", style="cyan", no_wrap=True, width=COLUMN_WIDTH)

        for tool in lock_file.tools:
            tool_yaml_contents = yaml.safe_load(
                Path(source / tool.path).read_text())
            tools_table.add_row(
                tool_yaml_contents.get("name", "N/A"),
                str(tool.path),
                str(tool.id),
            )

        console.print(tools_table)
