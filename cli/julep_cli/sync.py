import hashlib
import json
from pathlib import Path
from typing import Annotated

import typer
import yaml

from .app import app
from .models import (
    CreateAgentRequest,
    CreateTaskRequest,
    CreateToolRequest,
    LockedEntity,
    LockFileContents,
    Relationships,
    TaskAgentRelationship,
    ToolAgentRelationship,
)
from .utils import (
    get_julep_client,
    get_julep_yaml,
    write_lock_file,
)


@app.command()
def sync(
    source: Annotated[
        Path,
        typer.Option(
            "--source",
            "-s",
            help="Source directory containing julep.yaml",
        ),
    ] = Path.cwd(),
    force_local: Annotated[
        bool,
        typer.Option(
            "--force-local",
            help="Force local state to match remote",
        ),
    ] = False,
    force_remote: Annotated[
        bool,
        typer.Option(
            "--force-remote",
            help="Force remote state to match local",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="Simulate synchronization without making changes",
        ),
    ] = False,
):
    """Synchronize local package with Julep platform"""

    if dry_run:
        typer.echo("Dry run - no changes will be made")
        return

    if force_local and force_remote:
        typer.echo("Error: Cannot use both --force-local and --force-remote", err=True)
        raise typer.Exit(1)

    lock_file = source / "julep-lock.json"

    try:
        client = get_julep_client()
    except Exception as e:
        typer.echo(f"Error initializing Julep client: {e}", err=True)
        raise typer.Exit(1)

    if force_local and not lock_file.exists():
        locked_agents: list[LockedEntity] = []
        locked_tasks: list[LockedEntity] = []
        locked_tools: list[LockedEntity] = []
        relationships: Relationships = Relationships()

        julep_yaml_content = get_julep_yaml(source)
        agents: list[dict] = julep_yaml_content.get("agents", [])
        tasks: list[dict] = julep_yaml_content.get("tasks", [])
        tools: list[dict] = julep_yaml_content.get("tools", [])

        if agents or tasks or tools:
            typer.echo("Found the following new entities in julep.yaml:")
        else:
            typer.echo("No new entities found in julep.yaml")
            return

        if agents:
            typer.echo("Agents:")
            for agent in agents:
                typer.echo(f"  - {agent.get('definition')}")
        if tasks:
            typer.echo("Tasks:")
            for task in tasks:
                typer.echo(f"  - {task.get('definition')}")
        if tools:
            typer.echo("Tools:")
            for tool in tools:
                typer.echo(f"  - {tool.get('definition')}")

        if agents:
            # Create agents on remote
            typer.echo("Creating agents on remote...")
            for agent in agents:
                agent_yaml_path: Path = source / agent.pop("definition")
                agent_yaml_content = yaml.safe_load(agent_yaml_path.read_text())

                agent_request_hash = hashlib.sha256(
                    json.dumps(agent_yaml_content).encode()
                ).hexdigest()

                # Create agent request, giving priority to the attributes in julep.yaml
                agent_request = CreateAgentRequest(**agent_yaml_content, **agent)

                created_agent = client.agents.create(
                    **agent_request.model_dump(exclude_unset=True, exclude_none=True)
                )

                locked_agents.append(
                    LockedEntity(
                        path=str(agent_yaml_path.relative_to(source)),
                        id=created_agent.id,
                        last_synced=created_agent.created_at.isoformat(timespec="milliseconds")
                        + "Z",
                        revision_hash=agent_request_hash,
                    )
                )
            typer.echo("All agents were successfully created on remote")

        if tasks:
            typer.echo("Creating tasks on remote...")
            # Create tasks on remote
            for task in tasks:
                task_yaml_path: Path = source / task.pop("definition")

                agent_id_expression = task.pop("agent_id")
                agent_id = eval(f'f"{agent_id_expression}"', {"agents": locked_agents})

                task_yaml_content = yaml.safe_load(task_yaml_path.read_text())

                task_request_hash = hashlib.sha256(
                    json.dumps(task_yaml_content).encode()
                ).hexdigest()

                task_request = CreateTaskRequest(**task_yaml_content, **task)
                created_task = client.tasks.create(
                    agent_id=agent_id,
                    **task_request.model_dump(exclude_unset=True, exclude_none=True),
                )

                relationships.tasks.append(
                    TaskAgentRelationship(id=created_task.id, agent_id=agent_id)
                )

                locked_tasks.append(
                    LockedEntity(
                        path=str(task_yaml_path.relative_to(source)),
                        id=created_task.id,
                        last_synced=created_task.created_at.isoformat(timespec="milliseconds")
                        + "Z",
                        revision_hash=task_request_hash,
                    )
                )
            typer.echo("All tasks were successfully created on remote")
        
        if tools:
            typer.echo("Creating tools on remote...")
            # Create tools on remote
            for tool in tools:
                tool_yaml_path: Path = source / tool.pop("definition")
                tool_yaml_content = yaml.safe_load(tool_yaml_path.read_text())

                tool_request_hash = hashlib.sha256(
                    json.dumps(tool_yaml_content).encode()
                ).hexdigest()

                tool_request = CreateToolRequest(**tool_yaml_content, **tool)

                agent_id_expression = tool.pop("agent_id")
                agent_id = eval(f'f"{agent_id_expression}"', {"agents": locked_agents})

                created_tool = client.agents.tools.create(
                    agent_id=agent_id,
                    **tool_request.model_dump(exclude_unset=True, exclude_none=True),
                )

                relationships.tools.append(
                    ToolAgentRelationship(id=created_tool.id, agent_id=agent_id)
                )

                locked_tools.append(
                    LockedEntity(
                        path=str(tool_yaml_path.relative_to(source)),
                        id=created_tool.id,
                        last_synced=created_tool.created_at.isoformat(timespec="milliseconds")
                        + "Z",
                        revision_hash=tool_request_hash,
                    )
                )
            typer.echo("All tools were successfully created on remote")

        typer.echo("Creating lock file...")
        write_lock_file(
            source,
            LockFileContents(
                agents=locked_agents,
                tasks=locked_tasks,
                tools=locked_tools,
                relationships=relationships,
            ),
        )
        typer.echo("Lock file created successfully")

        return

    if force_remote:
        # TODO: Implement force remote here
        typer.echo("Force remote - not implemented")
        raise typer.Exit(1)

        # Fetch remote state
        # remote_agents: list[CreateAgentRequest] = fetch_all_remote_agents(client)

        # Fetch local from lock file

        # Compare local and remote states

    # TODO: Implement logic when no force flags are provided
