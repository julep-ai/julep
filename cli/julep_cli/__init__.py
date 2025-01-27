# ruff: noqa: RUF013

import io
import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Annotated

import requests
import typer
from environs import Env

# Initialize typer app
app = typer.Typer(
    name="julep",
    help="Command line interface for the Julep platform",
    no_args_is_help=True,
    pretty_exceptions_short=False,
)

# Initialize subcommands
agents_app = typer.Typer(help="Manage AI agents")
tasks_app = typer.Typer(help="Manage tasks")
tools_app = typer.Typer(help="Manage tools")

app.add_typer(agents_app, name="agents")
app.add_typer(tasks_app, name="tasks")
app.add_typer(tools_app, name="tools")

# Config handling
env = Env()
CONFIG_DIR = Path.home() / ".config" / "julep"
CONFIG_FILE_NAME = "config.yml"


def get_config(config_dir: Path = CONFIG_DIR):
    """Get configuration from config file"""
    if not (config_dir / CONFIG_FILE_NAME).exists():
        return {}
    import yaml

    with open(config_dir / CONFIG_FILE_NAME) as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict, config_dir: Path = CONFIG_DIR):
    """Save configuration to config file"""
    config_dir.mkdir(parents=True, exist_ok=True)
    import yaml

    with open(config_dir / CONFIG_FILE_NAME, "w") as f:
        yaml.dump(config, f)


# Auth command
@app.command()
def auth(
    api_key: Annotated[
        str,
        typer.Option(
            "--api-key",
            "-k",
            help="Your Julep API key",
            prompt="Please enter your Julep API key"
            if not os.getenv("JULEP_API_KEY")
            else False,
        ),
    ] = None,
):
    """Authenticate with the Julep platform"""
    api_key = api_key or os.getenv("JULEP_API_KEY")

    if not api_key:
        typer.echo("No API key provided", err=True)
        raise typer.Exit(1)

    config = get_config()
    config["api_key"] = api_key
    save_config(config)

    typer.echo("Successfully authenticated!")


# Version command
def version_callback(value: bool):
    if value:
        from importlib.metadata import version

        try:
            v = version("julep-cli")
            typer.echo(f"julep CLI version {v}")
        except:
            typer.echo("julep CLI version unknown")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
):
    """
    Julep CLI - Command line interface for the Julep platform
    """


# Sync command
@app.command()
def sync(
    source: Annotated[
        Path,
        typer.Option(
            "--source",
            "-s",
            help="Source directory containing julep.yaml",
        ),
    ],
    overwrite: Annotated[
        str,
        typer.Option(
            "--overwrite",
            "-o",
            help="How to handle conflicts: 'local' or 'remote'",
        ),
    ] = None,
    watch: Annotated[
        bool,
        typer.Option(
            "--watch",
            "-w",
            help="Watch for changes and sync automatically",
        ),
    ] = False,
):
    """Synchronize local package with Julep platform"""
    if not (source / "julep.yaml").exists():
        typer.echo("Error: julep.yaml not found in source directory", err=True)
        raise typer.Exit(1)

    # ... rest of sync implementation ...


# Chat command
@app.command()
def chat(
    agent: Annotated[str, typer.Option("--agent", "-a", help="Agent ID or name to chat with")],
    situation: Annotated[
        str, typer.Option("--situation", "-s", help="Situation to chat about")
    ] = None,
    history: Annotated[
        Path,
        typer.Option(
            "--history",
            "-h",
            help="Load chat history from file",
        ),
    ] = None,
    save_history: Annotated[
        Path,
        typer.Option(
            "--save-history",
            "-s",
            help="Save chat history to file",
        ),
    ] = None,
):
    """Start an interactive chat session with an agent"""
    # TODO: Implement chat logic
    typer.echo(f"Starting chat with agent '{agent}'")
    if situation:
        typer.echo(f"Context: {situation}")


# Run command
@app.command()
def run(
    task: Annotated[
        str,
        typer.Option(
            "--task",
            "-t",
            help="Task ID or name to execute",
        ),
    ],
    input: Annotated[
        str,
        typer.Option(
            "--input",
            "-i",
            help="JSON string of input parameters",
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="Simulate execution without making changes",
        ),
    ] = False,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Save output to file",
        ),
    ] = None,
):
    """Execute a task with provided inputs"""
    # TODO: Implement task execution logic
    typer.echo(f"Running task '{task}' with input: {input}")


# Agent management commands
@agents_app.command()
def create(
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the agent")],
    model: Annotated[str, typer.Option("--model", "-m", help="Model to be used by the agent")],
    about: Annotated[
        str, typer.Option("--about", "-a", help="Description of the agent")
    ] = None,
    metadata: Annotated[
        str, typer.Option("--metadata", help="JSON metadata for the agent")
    ] = None,
    default_settings: Annotated[
        str,
        typer.Option("--default-settings", help="JSON default settings for the agent"),
    ] = None,
    instructions: Annotated[
        list[str], typer.Option("--instructions", help="Instructions for the agent")
    ] = [],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="Simulate agent creation without making changes",
        ),
    ] = False,
):
    """Create a new AI agent"""
    try:
        metadata_dict = json.loads(metadata) if metadata else {}
        settings_dict = json.loads(default_settings) if default_settings else {}
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {e}", err=True)
        raise typer.Exit(1)

    if dry_run:
        typer.echo("Dry run - would create agent with:")
        typer.echo(f"  Name: {name}")
        typer.echo(f"  Model: {model}")
        typer.echo(f"  About: {about}")
        typer.echo(f"  Metadata: {metadata_dict}")
        typer.echo(f"  Default Settings: {settings_dict}")
        typer.echo(f"  Instructions: {instructions}")
        return

    # TODO: Implement actual API call
    typer.echo(f"Created agent '{name}' with model '{model}'")


@agents_app.command()
def update(
    agent_id: Annotated[str, typer.Option("--id", "-i", help="ID of the agent to update")],
    name: Annotated[str, typer.Option("--name", "-n", help="New name for the agent")] = None,
    model: Annotated[str, typer.Option("--model", "-m", help="New model for the agent")] = None,
    about: Annotated[
        str, typer.Option("--about", "-a", help="New description for the agent")
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="Simulate agent update without making changes",
        ),
    ] = False,
):
    """Update an existing AI agent"""
    updates = {
        k: v for k, v in {"name": name, "model": model, "about": about}.items() if v is not None
    }

    if not updates:
        typer.echo("No updates provided", err=True)
        raise typer.Exit(1)

    if dry_run:
        typer.echo("Dry run - would update agent with:")
        for key, value in updates.items():
            typer.echo(f"  {key}: {value}")
        return

    # TODO: Implement actual API call
    typer.echo(f"Updated agent '{agent_id}'")


@agents_app.command()
def list(
    filter: Annotated[
        str, typer.Option("--filter", "-f", help="Filter agents based on criteria")
    ] = None,
    metadata_filter: Annotated[
        str,
        typer.Option("--metadata-filter", help="Filter agents based on metadata criteria"),
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output the list in JSON format")
    ] = False,
):
    """List all AI agents"""
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
def delete(
    agent_id: Annotated[str, typer.Option("--id", "-i", help="ID of the agent to delete")],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force deletion without confirmation",
        ),
    ] = False,
):
    """Delete an AI agent"""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete agent '{agent_id}'?")
        if not confirm:
            typer.echo("Operation cancelled")
            raise typer.Exit

    # TODO: Implement actual API call
    typer.echo(f"Deleted agent '{agent_id}'")


@agents_app.command()
def reset(
    agent_id: Annotated[str, typer.Option("--id", "-i", help="ID of the agent to reset")],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force reset without confirmation",
        ),
    ] = False,
):
    """Reset an AI agent to its initial state"""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to reset agent '{agent_id}'?")
        if not confirm:
            typer.echo("Operation cancelled")
            raise typer.Exit

    # TODO: Implement actual API call
    typer.echo(f"Reset agent '{agent_id}' to initial state")


@agents_app.command()
def get(
    agent_id: Annotated[str, typer.Option("--id", "-i", help="ID of the agent to retrieve")],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output in JSON format")
    ] = False,
):
    """Get details of a specific AI agent"""
    # TODO: Implement actual API call
    # Mock data for demonstration
    agent = {
        "id": agent_id,
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


@app.command()
def init(
    template: Annotated[
        str,
        typer.Option(
            "--template",
            "-t",
            help="Template name to use",
        ),
    ] = "hello-world",
    output_dir: Annotated[
        Path,
        typer.Option(
            "--destination",
            "-o",
            help="Destination directory",
        ),
    ] = Path.cwd(),
):
    """Initialize a new Julep project"""
    repo_url = "https://github.com/julep-ai/library"
    branch = "main"
    template_url = f"{repo_url}/archive/refs/heads/{branch}.zip"

    try:
        # Download the repository as a zip file
        response = requests.get(template_url)
        response.raise_for_status()

        # Extract the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Construct the path to the template folder within the zip

            repo_prefix = f"library-{branch}/"

            template_folder = f"{repo_prefix}{template}/"
            # Extract only the specified template folder

            typer.echo(f"Extracting template '{template}' to {output_dir}")

            for file_info in z.infolist():
                if file_info.filename.startswith(template_folder):
                    # Remove the leading directory path

                    z.extract(file_info, output_dir)

                    library_repo_prefix = output_dir / f"library-{branch}"
                    # Move the inner template directory to the destination directory
                    extracted_template_path = library_repo_prefix / template
                    final_destination = output_dir / template

                    # Ensure the final destination directory exists
                    final_destination.mkdir(parents=True, exist_ok=True)

                    # Move files from the extracted template path to the final destination
                    for item in extracted_template_path.iterdir():
                        item.rename(final_destination / item.name)

                    # Remove the extracted template directory and its parent
                    shutil.rmtree(library_repo_prefix)

    except requests.exceptions.RequestException as e:
        typer.echo(f"Failed to download template: {e}", err=True)
        raise typer.Exit(1)
    except zipfile.BadZipFile as e:
        typer.echo(f"Failed to extract template: {e}", err=True)
        raise typer.Exit(1)

    julep_toml = output_dir / template / "julep.toml"
    if not julep_toml.exists():
        typer.echo("Error: 'julep.toml' not found in the destination directory", err=True)
        raise typer.Exit(1)

    typer.echo(f"Initialized new Julep project with template '{template}' in {output_dir}")


# Task management commands
@tasks_app.command()
def create(
    agent_id: Annotated[
        str,
        typer.Option("--agent-id", "-a", help="ID of the agent the task is associated with"),
    ],
    definition: Annotated[
        str, typer.Option("--definition", "-d", help="Path to the task definition YAML file")
    ],
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the task")] = None,
    description: Annotated[
        str, typer.Option("--description", help="Description of the task")
    ] = None,
    metadata: Annotated[
        str, typer.Option("--metadata", help="JSON metadata for the task")
    ] = None,
    inherit_tools: Annotated[
        bool, typer.Option("--inherit-tools", help="Inherit tools from the associated agent")
    ] = False,
):
    """Create a new task for an agent"""
    try:
        json.loads(metadata) if metadata else {}
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {e}", err=True)
        raise typer.Exit(1)

    # TODO: Implement actual API call
    typer.echo(f"Created task '{name}' for agent '{agent_id}'")


@tasks_app.command()
def update(
    task_id: Annotated[str, typer.Option("--id", help="ID of the task to update")],
    name: Annotated[str, typer.Option("--name", "-n", help="New name for the task")] = None,
    description: Annotated[
        str, typer.Option("--description", help="New description for the task")
    ] = None,
    definition: Annotated[
        str,
        typer.Option(
            "--definition", "-d", help="Path to the updated task definition YAML file"
        ),
    ] = None,
    metadata: Annotated[
        str, typer.Option("--metadata", help="JSON metadata for the task")
    ] = None,
    inherit_tools: Annotated[
        bool,
        typer.Option("--inherit-tools", help="Inherit tools from the associated agent"),
    ] = None,
):
    """Update an existing task"""
    try:
        json.loads(metadata) if metadata else {}
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {e}", err=True)
        raise typer.Exit(1)

    # TODO: Implement actual API call
    typer.echo(f"Updated task '{task_id}'")


@tasks_app.command()
def delete(
    task_id: Annotated[str, typer.Option("--id", help="ID of the task to delete")],
):
    """Delete an existing task"""
    # TODO: Implement actual API call
    typer.echo(f"Deleted task '{task_id}'")


@tasks_app.command()
def list(
    agent_id: Annotated[
        str, typer.Option("--agent-id", "-a", help="Filter tasks by associated agent ID")
    ] = None,
    filter: Annotated[
        str, typer.Option("--filter", "-f", help="Additional filter criteria")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output the list in JSON format")
    ] = False,
):
    """List all tasks or filter based on criteria"""
    # TODO: Implement actual API call
    # Mock data for demonstration
    tasks = [
        {"id": "task1", "name": "Test Task 1", "agent_id": "agent1"},
        {"id": "task2", "name": "Test Task 2", "agent_id": "agent2"},
    ]

    if json_output:
        typer.echo(json.dumps(tasks, indent=2))
        return

    # Table format output
    typer.echo("Available tasks:")
    typer.echo("ID\tName\tAgent ID")
    typer.echo("-" * 40)
    for task in tasks:
        typer.echo(f"{task['id']}\t{task['name']}\t{task['agent_id']}")


# Tool management commands
@tools_app.command()
def create(
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the tool")],
    tool_type: Annotated[
        str,
        typer.Option(
            "--type", "-t", help="Type of the tool (integration, api_call, function, system)"
        ),
    ],
    agent_id: Annotated[
        str,
        typer.Option("--agent-id", "-a", help="ID of the agent the tool is associated with"),
    ],
    config: Annotated[
        str, typer.Option("--config", "-c", help="Path to the tool configuration YAML file")
    ],
):
    """Create a new tool for an agent"""
    # TODO: Implement actual API call
    typer.echo(f"Created tool '{name}' of type '{tool_type}' for agent '{agent_id}'")


@tools_app.command()
def update(
    tool_id: Annotated[str, typer.Option("--id", help="ID of the tool to update")],
    name: Annotated[str, typer.Option("--name", "-n", help="New name for the tool")] = None,
    config: Annotated[
        str,
        typer.Option("--config", "-c", help="Path to the updated tool configuration YAML file"),
    ] = None,
):
    """Update an existing tool"""
    # TODO: Implement actual API call
    typer.echo(f"Updated tool '{tool_id}'")


@tools_app.command()
def delete(
    tool_id: Annotated[str, typer.Option("--id", help="ID of the tool to delete")],
):
    """Delete an existing tool"""
    # TODO: Implement actual API call
    typer.echo(f"Deleted tool '{tool_id}'")


@tools_app.command()
def list(
    agent_id: Annotated[
        str, typer.Option("--agent-id", "-a", help="Filter tools by associated agent ID")
    ] = None,
    tool_type: Annotated[str, typer.Option("--type", "-t", help="Filter tools by type")] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output the list in JSON format")
    ] = False,
):
    """List all tools or filter based on criteria"""
    # TODO: Implement actual API call
    # Mock data for demonstration
    tools = [
        {"id": "tool1", "name": "Web Search", "type": "integration", "agent_id": "agent1"},
        {"id": "tool2", "name": "API Call", "type": "api_call", "agent_id": "agent2"},
    ]

    if json_output:
        typer.echo(json.dumps(tools, indent=2))
        return

    # Table format output
    typer.echo("Available tools:")
    typer.echo("ID\tName\tType\tAgent ID")
    typer.echo("-" * 50)
    for tool in tools:
        typer.echo(f"{tool['id']}\t{tool['name']}\t{tool['type']}\t{tool['agent_id']}")
