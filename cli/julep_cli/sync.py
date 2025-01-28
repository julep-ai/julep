import hashlib
import json
from datetime import datetime
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
    get_lock_file,
    get_related_agent_id,
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

    if force_local and lock_file.exists():
        lock_file = get_lock_file(source)
        julep_yaml_content = get_julep_yaml(source)

        agents_julep_yaml = julep_yaml_content.get("agents", [])
        tasks_julep_yaml = julep_yaml_content.get("tasks", [])
        tools_julep_yaml = julep_yaml_content.get("tools", [])

        for agent_julep_yaml in agents_julep_yaml:
            agent_yaml_def_path: Path = Path(agent_julep_yaml.get("definition"))
            agent_yaml_content = yaml.safe_load(
                (source / agent_yaml_def_path).read_text())
            found_in_lock = False

            for i in range(len(lock_file.agents)):
                agent_julep_lock = lock_file.agents[i]

                if agent_julep_lock.path == str(agent_yaml_def_path):
                    found_in_lock = True
                    agent_yaml_content_hash = hashlib.sha256(json.dumps(agent_yaml_content).encode()).hexdigest()
                    agent_julep_lock_hash = agent_julep_lock.revision_hash

                    if agent_yaml_content_hash != agent_julep_lock_hash:
                        typer.echo(f"Agent {agent_yaml_def_path} has changed, updating on remote...")

                        agent_request = CreateAgentRequest(**agent_yaml_content, **agent_julep_yaml)

                        client.agents.create_or_update(agent_id=agent_julep_lock.id, **agent_request.model_dump(exclude_unset=True, exclude_none=True))

                        updated_at = client.agents.get(agent_julep_lock.id).updated_at
                        # Update the hash and last synced date in the lock file
                        lock_file.agents[i] = LockedEntity(
                            path=agent_julep_lock.path,
                            id=agent_julep_lock.id,
                            last_synced=updated_at.isoformat(timespec="milliseconds") + "Z",
                            revision_hash=agent_yaml_content_hash,
                        )
                    break

            if not found_in_lock:
                typer.echo(f"Agent {agent_yaml_def_path} not found in lock file, creating new agent...")

                agent_request_hash = hashlib.sha256(json.dumps(agent_yaml_content).encode()).hexdigest()

                agent_request = CreateAgentRequest(**agent_yaml_content, **agent_julep_yaml)
                created_agent = client.agents.create(**agent_request.model_dump(exclude_unset=True, exclude_none=True))

                lock_file.agents.append(LockedEntity(
                    path=str(agent_yaml_def_path),
                    id=created_agent.id,
                    last_synced=created_agent.created_at.isoformat(timespec="milliseconds") + "Z",
                    revision_hash=agent_request_hash,
                ))

                typer.echo(f"Agent {agent_yaml_def_path} created successfully on remote")

        for task_julep_yaml in tasks_julep_yaml:
            task_yaml_def_path: Path = Path(task_julep_yaml.get("definition"))
            task_yaml_content = yaml.safe_load(
                (source / task_yaml_def_path).read_text())
            found_in_lock = False

            for i in range(len(lock_file.tasks)):
                task_julep_lock = lock_file.tasks[i]

                if task_julep_lock.path == str(task_yaml_def_path):
                    found_in_lock = True
                    task_yaml_content_hash = hashlib.sha256(json.dumps(task_yaml_content).encode()).hexdigest()
                    task_julep_lock_hash = task_julep_lock.revision_hash

                    if task_yaml_content_hash != task_julep_lock_hash:
                        typer.echo(f"Task {task_yaml_def_path} has changed, updating on remote...")

                        task_request = CreateTaskRequest(**task_yaml_content, **task_julep_yaml)

                        agent_id = get_related_agent_id(task_julep_lock.id, lock_file.relationships.tasks)

                        if not agent_id:
                            typer.echo(f"Task {task_yaml_def_path} has no related agent. Please check the lock file and julep.yaml for consistency.")
                            raise typer.Exit(1)

                        client.tasks.create_or_update(task_id=task_julep_lock.id, agent_id=agent_id, **task_request.model_dump(exclude_unset=True, exclude_none=True))

                        updated_at = client.tasks.get(task_julep_lock.id).updated_at
                        lock_file.tasks[i] = LockedEntity(
                            path=task_julep_lock.path,
                            id=task_julep_lock.id,
                            last_synced=updated_at.isoformat(timespec="milliseconds") + "Z",
                            revision_hash=task_yaml_content_hash,
                        )
                    break

            if not found_in_lock:
                typer.echo(f"Task {task_yaml_def_path} not found in lock file, creating new task...")

                task_request_hash = hashlib.sha256(json.dumps(task_yaml_content).encode()).hexdigest()

                # Get the agent id from the julep.yaml file
                agent_id_expression = task_julep_yaml.pop("agent_id")
                agent_id = eval(f'f"{agent_id_expression}"', {"agents": lock_file.agents})

                task_request = CreateTaskRequest(**task_yaml_content, **task_julep_yaml)
                created_task = client.tasks.create(agent_id=agent_id, **task_request.model_dump(exclude_unset=True, exclude_none=True))

                lock_file.tasks.append(LockedEntity(
                    path=str(task_yaml_def_path),
                    id=created_task.id,
                    last_synced=created_task.created_at.isoformat(timespec="milliseconds") + "Z",
                    revision_hash=task_request_hash,
                ))

                # Add the task dependency to the relationships
                lock_file.relationships.tasks.append(TaskAgentRelationship(id=created_task.id, agent_id=agent_id))

                typer.echo(f"Task {task_yaml_def_path} created successfully on remote")

        for tool_julep_yaml in tools_julep_yaml:
            tool_yaml_def_path: Path = Path(tool_julep_yaml.get("definition"))
            tool_yaml_content = yaml.safe_load((source / tool_yaml_def_path).read_text())
            found_in_lock = False

            for i in range(len(lock_file.tools)):
                tool_julep_lock = lock_file.tools[i]

                if tool_julep_lock.path == str(tool_yaml_def_path):
                    found_in_lock = True
                    tool_yaml_content_hash = hashlib.sha256(json.dumps(tool_yaml_content).encode()).hexdigest()
                    tool_julep_lock_hash = tool_julep_lock.revision_hash

                    if tool_yaml_content_hash != tool_julep_lock_hash:
                        typer.echo(f"Tool {tool_yaml_def_path} has changed, updating on remote...")

                        tool_request = CreateToolRequest(**tool_yaml_content, **tool_julep_yaml)

                        agent_id = get_related_agent_id(tool_julep_lock.id, lock_file.relationships.tools)

                        if not agent_id:
                            typer.echo(f"Tool {tool_yaml_def_path} has no related agent. Please check the lock file and julep.yaml for consistency.")
                            raise typer.Exit(1)

                        client.agents.tools.update(tool_id=tool_julep_lock.id, agent_id=agent_id, **tool_request.model_dump(exclude_unset=True, exclude_none=True))

                        # There is no way to get the updated_at date from the API, so we use the current date
                        # updated_at = client.agents.tools.get(tool_julep_lock.id).updated_at

                        lock_file.tools[i] = LockedEntity(
                            path=tool_julep_lock.path,
                            id=tool_julep_lock.id,
                            last_synced=datetime.now().isoformat(timespec="milliseconds") + "Z",
                            revision_hash=tool_yaml_content_hash,
                        )
                    break

            if not found_in_lock:
                typer.echo(f"Tool {tool_yaml_def_path} not found in lock file, creating new tool...")

                tool_request_hash = hashlib.sha256(json.dumps(tool_yaml_content).encode()).hexdigest()

                # Get the agent id from the julep.yaml file
                agent_id_expression = tool_julep_yaml.pop("agent_id")
                agent_id = eval(f'f"{agent_id_expression}"', {"agents": lock_file.agents})

                tool_request = CreateToolRequest(**tool_yaml_content, **tool_julep_yaml)
                created_tool = client.agents.tools.create(agent_id=agent_id, **tool_request.model_dump(exclude_unset=True, exclude_none=True))

                lock_file.tools.append(LockedEntity(
                    path=str(tool_yaml_def_path),
                    id=created_tool.id,
                    last_synced=created_tool.created_at.isoformat(timespec="milliseconds") + "Z",
                    revision_hash=tool_request_hash,
                ))

                # Add the tool dependency to the relationships
                lock_file.relationships.tools.append(ToolAgentRelationship(id=created_tool.id, agent_id=agent_id))

                typer.echo(f"Tool {tool_yaml_def_path} created successfully on remote")

        write_lock_file(source, lock_file)

    if force_remote:
        # TODO: Implement force remote here
        typer.echo("Force remote - not implemented")
        raise typer.Exit(1)

        # Fetch remote state
        # remote_agents: list[CreateAgentRequest] = fetch_all_remote_agents(client)

        # Fetch local from lock file

        # Compare local and remote states

    # TODO: Implement logic when no force flags are provided
