import hashlib
import json
import threading
import time
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import julep
import typer
import yaml
from julep.types import Agent, Task
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .app import app, console, error_console, local_tz
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
    get_agent_id_from_expression,
    get_julep_client,
    get_julep_yaml,
    get_lock_file,
    get_related_agent_id,
    update_entity_force_remote,
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
    watch: Annotated[
        bool,
        typer.Option(
            "--watch",
            "-w",
            help=(
                "Watch for changes and synchronize automatically. Note: when watch mode is enabled, "
                "only local-to-remote sync (force-local) is supported. Use --force-remote only with watch mode turned off."
            ),
        ),
    ] = False,
):
    """Synchronize local package with Julep platform.

    Note: When watch mode is enabled, local changes are continuously synced to remote
    (i.e. the process works as 'force-local' and --force-remote is ignored).
    """
    # set the lock file path
    lock_file_path = source / "julep-lock.json"

    # if dry_run is true, we print a dry run message
    if dry_run:
        console.print(Text("Dry run - no changes will be made", style="bold yellow"))
        return

    # if force_local is false and force_remote is false and lock file does not exist, we set force_local to true
    if not force_local and not force_remote and not lock_file_path.exists():
        force_local = True

    # if watch is true and force_remote is true, we raise an error
    if watch and force_remote:
        error_console.print(
            Text("Error: Cannot use both --watch and --force-remote", style="bold red")
        )
        raise typer.Exit(1)

    # When watch mode is enabled, force a local sync and disable remote forcing.
    if watch:
        if force_remote:
            error_console.print(
                Text("Error: Cannot use both --watch and --force-remote", style="bold red")
            )
            raise typer.Exit(1)
        console.print(
            Text(
                "Watch mode enabled. Forcing local sync and disabling force_remote.",
                style="bold green",
            )
        )
        force_local = True
        force_remote = False

    # Wrap the sync logic in an inner function to allow re-running on file changes.
    def perform_sync_logic():
        try:
            client = get_julep_client()
        except Exception as e:
            error_console.print(Text(f"Error initializing Julep client: {e}", style="bold red"))
            if not watch:
                raise typer.Exit(1)
            return

        # Branch A: If forcing local sync and no lock file exists
        if force_local and not lock_file_path.exists():
            locked_agents: list[LockedEntity] = []
            locked_tasks: list[LockedEntity] = []
            locked_tools: list[LockedEntity] = []
            relationships: Relationships = Relationships()

            julep_yaml_content = get_julep_yaml(source)
            agents: list[dict] = julep_yaml_content.get("agents", [])
            tasks: list[dict] = julep_yaml_content.get("tasks", [])
            tools: list[dict] = julep_yaml_content.get("tools", [])

            if agents or tasks or tools:
                console.print(
                    Panel(
                        Text(
                            "Found the following new entities in julep.yaml:", style="bold cyan"
                        )
                    )
                )
                from rich.table import Table

                if agents:
                    table = Table(title="Agents", show_header=False, title_style="bold magenta")
                    table.add_column("Definition", style="dim", width=50)
                    for agent in agents:
                        table.add_row(agent.get("definition"))
                    console.print(table, highlight=True)

                if tasks:
                    table = Table(title="Tasks", show_header=False, title_style="bold cyan")
                    table.add_column("Definition", style="dim", width=50)
                    for task in tasks:
                        table.add_row(task.get("definition"))
                    console.print(table, highlight=True)

                if tools:
                    table = Table(title="Tools", show_header=False, title_style="bold green")
                    table.add_column("Definition", style="dim", width=50)
                    for tool in tools:
                        table.add_row(tool.get("definition"))
                    console.print(table, highlight=True)
            else:
                console.print(Text("No new entities found in julep.yaml", style="bold yellow"))
                return

            if agents:
                for agent in agents:
                    agent_yaml_path: Path = source / agent.pop("definition")
                    agent_yaml_content = yaml.safe_load(agent_yaml_path.read_text())
                    agent_request_hash = hashlib.sha256(
                        json.dumps(agent_yaml_content).encode()
                    ).hexdigest()
                    agent_request = CreateAgentRequest(**agent_yaml_content, **agent)

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True,
                        console=console,
                    ) as progress:
                        sync_task = progress.add_task(
                            "Creating agents on remote...", start=False
                        )
                        progress.start_task(sync_task)
                        created_agent = client.agents.create(
                            **agent_request.model_dump(exclude_unset=True, exclude_none=True)
                        )

                    locked_agents.append(
                        LockedEntity(
                            path=str(agent_yaml_path.relative_to(source)),
                            id=created_agent.id,
                            last_synced=created_agent.created_at.isoformat(
                                timespec="milliseconds"
                            )
                            + "Z",
                            revision_hash=agent_request_hash,
                        )
                    )
                console.print(
                    Text("All agents were successfully created on remote", style="bold green")
                )

            if tasks:
                for task in tasks:
                    task_yaml_path: Path = source / task.pop("definition")
                    agent_id = get_agent_id_from_expression(task.pop("agent_id"), locked_agents)
                    task_yaml_content = yaml.safe_load(task_yaml_path.read_text())
                    task_request_hash = hashlib.sha256(
                        json.dumps(task_yaml_content).encode()
                    ).hexdigest()
                    task_request = CreateTaskRequest(**task_yaml_content, **task)

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True,
                        console=console,
                    ) as progress:
                        sync_task = progress.add_task(
                            "Creating tasks on remote...", start=False
                        )
                        progress.start_task(sync_task)
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
                            last_synced=created_task.created_at.isoformat(
                                timespec="milliseconds"
                            )
                            + "Z",
                            revision_hash=task_request_hash,
                        )
                    )
                console.print(
                    Text("All tasks were successfully created on remote", style="bold blue")
                )

            if tools:
                for tool in tools:
                    tool_yaml_path: Path = source / tool.pop("definition")
                    tool_yaml_content = yaml.safe_load(tool_yaml_path.read_text())
                    tool_request_hash = hashlib.sha256(
                        json.dumps(tool_yaml_content).encode()
                    ).hexdigest()
                    tool_request = CreateToolRequest(**tool_yaml_content, **tool)

                    agent_id = get_agent_id_from_expression(tool.pop("agent_id"), locked_agents)

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True,
                        console=console,
                    ) as progress:
                        sync_task = progress.add_task(
                            "Creating tools on remote...", start=False
                        )
                        progress.start_task(sync_task)
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
                            last_synced=created_tool.created_at.isoformat(
                                timespec="milliseconds"
                            )
                            + "Z",
                            revision_hash=tool_request_hash,
                        )
                    )
                console.print(
                    Text("All tools were successfully created on remote", style="bold magenta")
                )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
                console=console,
            ) as progress:
                sync_task = progress.add_task("Writing lock file...", start=False)
                progress.start_task(sync_task)
                write_lock_file(
                    source,
                    LockFileContents(
                        agents=locked_agents,
                        tasks=locked_tasks,
                        tools=locked_tools,
                        relationships=relationships,
                    ),
                )

            console.print(Text("Synchronization complete", style="bold green"))
            return

        # Branch B: Force local update when lock file exists
        if force_local and lock_file_path.exists():
            found_changes = False
            lock_file = get_lock_file(source)
            julep_yaml_content = get_julep_yaml(source)

            agents_julep_yaml = julep_yaml_content.get("agents", [])
            tasks_julep_yaml = julep_yaml_content.get("tasks", [])
            tools_julep_yaml = julep_yaml_content.get("tools", [])

            # Update agents
            for agent_julep_yaml in agents_julep_yaml:
                agent_yaml_def_path: Path = Path(agent_julep_yaml.get("definition"))
                agent_yaml_content = yaml.safe_load((source / agent_yaml_def_path).read_text())
                found_in_lock = False

                for i in range(len(lock_file.agents)):
                    agent_julep_lock = lock_file.agents[i]
                    if agent_julep_lock.path == str(agent_yaml_def_path):
                        found_in_lock = True
                        agent_yaml_content_hash = hashlib.sha256(
                            json.dumps(agent_yaml_content).encode()
                        ).hexdigest()
                        agent_julep_lock_hash = agent_julep_lock.revision_hash

                        if agent_yaml_content_hash != agent_julep_lock_hash:
                            found_changes = True
                            console.print(
                                Text(
                                    f"Agent {agent_yaml_def_path} has changed, updating on remote...",
                                    style="bold yellow",
                                )
                            )

                            agent_request = CreateAgentRequest(
                                **agent_yaml_content, **agent_julep_yaml
                            )

                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[progress.description]{task.description}"),
                                transient=True,
                                console=console,
                            ) as progress:
                                sync_task = progress.add_task(
                                    "Updating agent on remote...", start=False
                                )
                                progress.start_task(sync_task)

                                try:
                                    client.agents.create_or_update(
                                        agent_id=agent_julep_lock.id,
                                        **agent_request.model_dump(
                                            exclude_unset=True, exclude_none=True
                                        ),
                                    )
                                except Exception as e:
                                    error_console.print(
                                        f"\n[bold red]Error updating agent: {e}[/bold red]"
                                    )
                                    raise typer.Exit(1)

                            console.print(
                                Text(
                                    f"Agent {agent_yaml_def_path} updated successfully",
                                    style="bold blue",
                                )
                            )

                            updated_at = client.agents.get(agent_julep_lock.id).updated_at
                            lock_file.agents[i] = LockedEntity(
                                path=agent_julep_lock.path,
                                id=agent_julep_lock.id,
                                last_synced=updated_at.isoformat(timespec="milliseconds") + "Z",
                                revision_hash=agent_yaml_content_hash,
                            )
                        break

                if not found_in_lock:
                    console.print(
                        Text(
                            f"Agent {agent_yaml_def_path} not found in lock file.",
                            style="bold yellow",
                        )
                    )

                    agent_request_hash = hashlib.sha256(
                        json.dumps(agent_yaml_content).encode()
                    ).hexdigest()

                    agent_request = CreateAgentRequest(**agent_yaml_content, **agent_julep_yaml)

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True,
                        console=console,
                    ) as progress:
                        sync_task = progress.add_task(
                            "Creating agent on remote...", start=False
                        )
                        progress.start_task(sync_task)

                        created_agent = client.agents.create(
                            **agent_request.model_dump(exclude_unset=True, exclude_none=True)
                        )

                    console.print(
                        Text(
                            f"Agent {agent_yaml_def_path} created successfully on remote",
                            style="bold blue",
                        )
                    )

                    lock_file.agents.append(
                        LockedEntity(
                            path=str(agent_yaml_def_path),
                            id=created_agent.id,
                            last_synced=created_agent.created_at.isoformat(
                                timespec="milliseconds"
                            )
                            + "Z",
                            revision_hash=agent_request_hash,
                        )
                    )

            # Update tasks
            for task_julep_yaml in tasks_julep_yaml:
                task_yaml_def_path: Path = Path(task_julep_yaml.get("definition"))
                task_yaml_content = yaml.safe_load((source / task_yaml_def_path).read_text())
                found_in_lock = False

                for i in range(len(lock_file.tasks)):
                    task_julep_lock = lock_file.tasks[i]

                    if task_julep_lock.path == str(task_yaml_def_path):
                        found_in_lock = True
                        task_yaml_content_hash = hashlib.sha256(
                            json.dumps(task_yaml_content).encode()
                        ).hexdigest()
                        task_julep_lock_hash = task_julep_lock.revision_hash

                        if task_yaml_content_hash != task_julep_lock_hash:
                            console.print(
                                Text(
                                    f"Task {task_yaml_def_path} has changed, updating on remote...",
                                    style="bold yellow",
                                )
                            )
                            found_changes = True

                            task_request = CreateTaskRequest(**{
                                **task_yaml_content,
                                **task_julep_yaml,
                            })

                            agent_id = get_related_agent_id(
                                task_julep_lock.id, lock_file.relationships.tasks
                            )

                            if not agent_id:
                                error_console.print(
                                    Text(
                                        f"Task {task_yaml_def_path} has no related agent. Please check the lock file and julep.yaml for consistency.",
                                        style="bold red",
                                    )
                                )
                                raise typer.Exit(1)

                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[progress.description]{task.description}"),
                                transient=True,
                                console=console,
                            ) as progress:
                                sync_task = progress.add_task(
                                    "Updating task on remote...", start=False
                                )
                                progress.start_task(sync_task)

                                client.tasks.create_or_update(
                                    task_id=task_julep_lock.id,
                                    agent_id=agent_id,
                                    **task_request.model_dump(
                                        exclude_unset=True, exclude_none=True
                                    ),
                                )

                            console.print(
                                Text(
                                    f"Task {task_yaml_def_path} updated successfully",
                                    style="bold blue",
                                )
                            )

                            updated_at = client.tasks.get(task_julep_lock.id).updated_at
                            lock_file.tasks[i] = LockedEntity(
                                path=task_julep_lock.path,
                                id=task_julep_lock.id,
                                last_synced=updated_at.isoformat(timespec="milliseconds") + "Z",
                                revision_hash=task_yaml_content_hash,
                            )
                        break

                if not found_in_lock:
                    console.print(
                        Text(
                            f"Task {task_yaml_def_path} not found in lock file, creating new task...",
                            style="bold yellow",
                        )
                    )

                    task_request_hash = hashlib.sha256(
                        json.dumps(task_yaml_content).encode()
                    ).hexdigest()

                    agent_id = get_agent_id_from_expression(
                        task_julep_yaml.pop("agent_id"), lock_file.agents
                    )

                    task_request = CreateTaskRequest(**task_yaml_content, **task_julep_yaml)

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True,
                        console=console,
                    ) as progress:
                        sync_task = progress.add_task("Creating task on remote...", start=False)
                        progress.start_task(sync_task)

                        created_task = client.tasks.create(
                            agent_id=agent_id,
                            **task_request.model_dump(exclude_unset=True, exclude_none=True),
                        )

                    lock_file.tasks.append(
                        LockedEntity(
                            path=str(task_yaml_def_path),
                            id=created_task.id,
                            last_synced=created_task.created_at.isoformat(
                                timespec="milliseconds"
                            )
                            + "Z",
                            revision_hash=task_request_hash,
                        )
                    )

                    lock_file.relationships.tasks.append(
                        TaskAgentRelationship(id=created_task.id, agent_id=agent_id)
                    )

                    console.print(
                        Text(
                            f"Task {task_yaml_def_path} created successfully on remote",
                            style="bold blue",
                        )
                    )

            # Update tools
            for tool_julep_yaml in tools_julep_yaml:
                tool_yaml_def_path: Path = Path(tool_julep_yaml.get("definition"))
                tool_yaml_content = yaml.safe_load((source / tool_yaml_def_path).read_text())
                found_in_lock = False

                for i in range(len(lock_file.tools)):
                    tool_julep_lock = lock_file.tools[i]

                    if tool_julep_lock.path == str(tool_yaml_def_path):
                        found_in_lock = True

                        tool_yaml_content_hash = hashlib.sha256(
                            json.dumps(tool_yaml_content).encode()
                        ).hexdigest()
                        tool_julep_lock_hash = tool_julep_lock.revision_hash

                        if tool_yaml_content_hash != tool_julep_lock_hash:
                            found_changes = True
                            console.print(
                                Text(
                                    f"Tool {tool_yaml_def_path} has changed, updating on remote...",
                                    style="bold yellow",
                                ),
                                highlight=True,
                            )

                            tool_request = CreateToolRequest(
                                **tool_yaml_content, **tool_julep_yaml
                            )

                            agent_id = get_related_agent_id(
                                tool_julep_lock.id, lock_file.relationships.tools
                            )

                            if not agent_id:
                                error_console.print(
                                    Text(
                                        f"Tool {tool_yaml_def_path} has no related agent. Please check the lock file and julep.yaml for consistency.",
                                        style="bold red",
                                    ),
                                    highlight=True,
                                )
                                raise typer.Exit(1)

                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[progress.description]{task.description}"),
                                transient=True,
                                console=console,
                            ) as progress:
                                sync_task = progress.add_task(
                                    "Updating tool on remote...", start=False
                                )
                                progress.start_task(sync_task)

                                client.agents.tools.update(
                                    tool_id=tool_julep_lock.id,
                                    agent_id=agent_id,
                                    **tool_request.model_dump(
                                        exclude_unset=True, exclude_none=True
                                    ),
                                )

                            console.print(
                                Text(
                                    f"Tool {tool_yaml_def_path} updated successfully",
                                    style="bold blue",
                                ),
                                highlight=True,
                            )

                            lock_file.tools[i] = LockedEntity(
                                path=tool_julep_lock.path,
                                id=tool_julep_lock.id,
                                last_synced=datetime.now(tz=local_tz).isoformat(
                                    timespec="milliseconds"
                                )
                                + "Z",
                                revision_hash=tool_yaml_content_hash,
                            )
                        break

                if not found_in_lock:
                    console.print(
                        Text(
                            f"Tool {tool_yaml_def_path} not found in lock file, creating new tool...",
                            style="bold yellow",
                        ),
                        highlight=True,
                    )

                    tool_request_hash = hashlib.sha256(
                        json.dumps(tool_yaml_content).encode()
                    ).hexdigest()

                    agent_id = get_agent_id_from_expression(
                        tool_julep_yaml.pop("agent_id"), lock_file.agents
                    )

                    tool_request = CreateToolRequest(**tool_yaml_content, **tool_julep_yaml)

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True,
                        console=console,
                    ) as progress:
                        sync_task = progress.add_task("Creating tool on remote...", start=False)
                        progress.start_task(sync_task)

                        created_tool = client.agents.tools.create(
                            agent_id=agent_id,
                            **tool_request.model_dump(exclude_unset=True, exclude_none=True),
                        )

                    lock_file.tools.append(
                        LockedEntity(
                            path=str(tool_yaml_def_path),
                            id=created_tool.id,
                            last_synced=created_tool.created_at.isoformat(
                                timespec="milliseconds"
                            )
                            + "Z",
                            revision_hash=tool_request_hash,
                        )
                    )

                    lock_file.relationships.tools.append(
                        ToolAgentRelationship(id=created_tool.id, agent_id=agent_id)
                    )

                    console.print(
                        Text(
                            f"Tool {tool_yaml_def_path} created successfully on remote",
                            style="bold blue",
                        ),
                        highlight=True,
                    )

            if found_changes:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True,
                    console=console,
                ) as progress:
                    sync_task = progress.add_task("Writing lock file...", start=False)
                    progress.start_task(sync_task)
                    write_lock_file(source, lock_file)

                console.print(
                    Text("Synchronization complete", style="bold green"), highlight=True
                )
                return

            console.print(
                Text("No changes detected. Everything is up to date.", style="bold green")
            )
            return

        # Branch C: Remote-to-local sync (when force_local is not used)
        lock_file = get_lock_file(source)
        detected_changes = False

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            sync_task = progress.add_task("Syncing agents...", start=False)
            progress.start_task(sync_task)

            remote_agents: list[Agent] = []
            agents_update_happened = False

            for locked_agent in lock_file.agents:
                try:
                    remote_agent = client.agents.get(locked_agent.id)
                    remote_agents.append(remote_agent)
                except julep.NotFoundError:
                    error_console.print(
                        Text(
                            f"Agent {locked_agent.id} not found on remote. It will be removed from the lock file.",
                            style="bold red",
                        ),
                        highlight=True,
                    )
                    console.print(
                        Text(
                            "- If you wish to create it again, please run `julep sync --force-local`",
                            style="bold yellow",
                        ),
                        highlight=True,
                    )
                    console.print(
                        Text(
                            f"- If this was intentional, please remove it from julep.yaml and delete the corresponding {locked_agent.path} file",
                            style="bold yellow",
                        ),
                        highlight=True,
                    )
                    lock_file.agents.remove(locked_agent)

            for i in range(len(lock_file.agents)):
                remote_agent, local_agent = remote_agents[i], lock_file.agents[i]
                assert remote_agent.id == local_agent.id

                last_synced_dt = datetime.fromisoformat(
                    local_agent.last_synced.rstrip("Z")
                ).replace(tzinfo=UTC)

                if remote_agent.updated_at > last_synced_dt:
                    detected_changes = True

                    progress.stop()

                    wants_to_update = force_remote or typer.confirm(
                        f"Agent {local_agent.path} has changed on remote. Do you want to update it locally?"
                    )

                    progress.start()

                    if wants_to_update:
                        lock_file.agents[i] = update_entity_force_remote(
                            entity=local_agent, remote_entity=remote_agent, source=source
                        )
                        agents_update_happened = True

            if agents_update_happened:
                console.print(
                    Text("Agents updated successfully", style="bold green"), highlight=True
                )
            else:
                console.print(Text("No agents updated", style="bold yellow"), highlight=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            sync_task = progress.add_task("Syncing tasks...", start=False)
            progress.start_task(sync_task)

            remote_tasks: list[Task] = []
            tasks_update_happened = False

            for locked_task in lock_file.tasks:
                try:
                    remote_task = client.tasks.get(locked_task.id)
                    remote_tasks.append(remote_task)
                except julep.NotFoundError:
                    error_console.print(
                        Text(
                            f"Task {locked_task.id} not found on remote. It will be removed from the lock file.",
                            style="bold red",
                        ),
                        highlight=True,
                    )

                    console.print(
                        Text(
                            "- If you wish to create it again, please run `julep sync --force-local`",
                            style="bold yellow",
                        )
                    )
                    console.print(
                        Text(
                            f"- If this was intentional, please remove it from julep.yaml and delete the corresponding {locked_task.path} file",
                            style="bold yellow",
                        )
                    )
                    lock_file.tasks.remove(locked_task)
                    raise typer.Exit(1)

            for i in range(len(lock_file.tasks)):
                remote_task, local_task = remote_tasks[i], lock_file.tasks[i]
                assert remote_task.id == local_task.id

                last_synced_dt = datetime.fromisoformat(
                    local_task.last_synced.rstrip("Z")
                ).replace(tzinfo=UTC)

                if remote_task.updated_at > last_synced_dt:
                    detected_changes = True

                    progress.stop()

                    wants_to_update = force_remote or typer.confirm(
                        f"Task {local_task.path} has changed on remote. Do you want to update it locally?"
                    )

                    progress.start()

                    if wants_to_update:
                        lock_file.tasks[i] = update_entity_force_remote(
                            entity=local_task, remote_entity=remote_task, source=source
                        )
                        tasks_update_happened = True

            if tasks_update_happened:
                console.print(Text("Tasks updated successfully", style="bold green"))
            else:
                console.print(Text("No tasks updated", style="bold yellow"))

        if agents_update_happened or tasks_update_happened:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                write_lock_task = progress.add_task("Writing lock file...", start=False)
                progress.start_task(write_lock_task)
                write_lock_file(source, lock_file)

            console.print(Text("Synchronization complete", style="bold green"), highlight=True)
        elif detected_changes:
            console.print(
                Text("No updates were made. Synchronization complete.", style="bold green"),
                highlight=True,
            )
        else:
            console.print(
                Text("No changes detected. Everything is up to date.", style="bold green"),
                highlight=True,
            )
        return

    if watch:
        console.print(
            Text("Starting watch mode. Monitoring YAML changes...", style="bold green")
        )
        # Run initial sync
        perform_sync_logic()

        # Debounced event handler to avoid rapid repeat syncs.
        class DebouncedYamlEventHandler(FileSystemEventHandler):
            def __init__(self, debounce_interval, callback):
                super().__init__()
                self.debounce_interval = debounce_interval
                self.callback = callback
                self.timer = None

            def _trigger_sync(self):
                self.timer = None

                with suppress(Exception):
                    self.callback()

            def on_modified(self, event):
                if event.src_path.endswith((".yaml", ".yml")):
                    console.print(
                        Text(
                            f"Change detected in {event.src_path}.\nSynchronizing...",
                            style="yellow",
                        )
                    )
                    if self.timer:
                        self.timer.cancel()
                    self.timer = threading.Timer(self.debounce_interval, self._trigger_sync)
                    self.timer.start()

            def on_created(self, event):
                if event.src_path.endswith((".yaml", ".yml")):
                    console.print(
                        Text(
                            f"New file {event.src_path} detected.\nSynchronizing...",
                            style="yellow",
                        )
                    )
                    if self.timer:
                        self.timer.cancel()
                    self.timer = threading.Timer(self.debounce_interval, self._trigger_sync)
                    self.timer.start()

        observer = Observer()
        # Set debounce_interval in seconds (e.g., 1.0 second)
        observer.schedule(
            DebouncedYamlEventHandler(1.0, perform_sync_logic), str(source), recursive=True
        )
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
        return
    perform_sync_logic()
    return
