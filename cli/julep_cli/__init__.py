import json
import os
from pathlib import Path

import typer
from environs import Env

# Initialize typer app
app = typer.Typer(
    name="julep", help="Command line interface for the Julep platform", no_args_is_help=True
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
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        "-k",
        help="Your Julep API key",
        prompt="Please enter your Julep API key" if not os.getenv("JULEP_API_KEY") else False,
    ),
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
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    """
    Julep CLI - Command line interface for the Julep platform
    """


# Init command
@app.command()
def init(
    template: str = typer.Option(
        ...,
        "--template",
        "-t",
        help="Template name to use",
    ),
    destination: Path = typer.Option(
        Path.cwd(),
        "--destination",
        "-d",
        help="Destination directory",
    ),
):
    """Initialize a new Julep project"""
    # TODO: Implement template copying logic
    typer.echo(f"Initializing new project from template '{template}' in {destination}")


# Sync command
@app.command()
def sync(
    source: Path = typer.Option(
        ...,
        "--source",
        "-s",
        help="Source directory containing julep.toml",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force synchronization",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Simulate synchronization without making changes",
    ),
):
    """Synchronize local package with Julep platform"""
    if not (source / "julep.toml").exists():
        typer.echo("Error: julep.toml not found in source directory", err=True)
        raise typer.Exit(1)

    if dry_run:
        typer.echo("Dry run - no changes will be made")

    # TODO: Implement sync logic
    typer.echo(f"Syncing project from {source}")


# Chat command
@app.command()
def chat(
    agent: str = typer.Option(..., "--agent", "-a", help="Agent ID or name to chat with"),
    history: Path | None = typer.Option(
        None,
        "--history",
        "-h",
        help="Load chat history from file",
    ),
    save_history: Path | None = typer.Option(
        None,
        "--save-history",
        "-s",
        help="Save chat history to file",
    ),
):
    """Start an interactive chat session with an agent"""
    # TODO: Implement chat logic
    typer.echo(f"Starting chat with agent '{agent}'")


# Run command
@app.command()
def run(
    task: str = typer.Option(
        ...,
        "--task",
        "-t",
        help="Task ID or name to execute",
    ),
    input: str = typer.Option(
        ...,
        "--input",
        "-i",
        help="JSON string of input parameters",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Simulate execution without making changes",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Save output to file",
    ),
):
    """Execute a task with provided inputs"""
    # TODO: Implement task execution logic
    typer.echo(f"Running task '{task}' with input: {input}")


# Agent management commands
@agents_app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="Name of the agent"),
    model: str = typer.Option(..., "--model", "-m", help="Model to be used by the agent"),
    about: str = typer.Option(None, "--about", "-a", help="Description of the agent"),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Simulate agent creation without making changes",
    ),
):
    """Create a new AI agent"""
    if dry_run:
        typer.echo("Dry run - would create agent with:")
        typer.echo(f"  Name: {name}")
        typer.echo(f"  Model: {model}")
        typer.echo(f"  About: {about}")
        return

    # TODO: Implement actual API call
    typer.echo(f"Created agent '{name}' with model '{model}'")


@agents_app.command()
def update(
    agent_id: str = typer.Option(..., "--id", "-i", help="ID of the agent to update"),
    name: str | None = typer.Option(None, "--name", "-n", help="New name for the agent"),
    model: str | None = typer.Option(None, "--model", "-m", help="New model for the agent"),
    about: str | None = typer.Option(
        None, "--about", "-a", help="New description for the agent"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Simulate agent update without making changes",
    ),
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
    filter: str | None = typer.Option(
        None, "--filter", "-f", help="Filter agents based on criteria"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output the list in JSON format"
    ),
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
    agent_id: str = typer.Option(..., "--id", "-i", help="ID of the agent to delete"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force deletion without confirmation",
    ),
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
    agent_id: str = typer.Option(..., "--id", "-i", help="ID of the agent to reset"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force reset without confirmation",
    ),
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
    agent_id: str = typer.Option(..., "--id", "-i", help="ID of the agent to retrieve"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format"),
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


if __name__ == "__main__":
    app()
