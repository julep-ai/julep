from pathlib import Path
import yaml
import typer
from julep import Julep
from .models import CreateAgentRequest, LockFileContents
import json

CONFIG_DIR = Path.home() / ".config" / "julep"
CONFIG_FILE_NAME = "config.yml"


def get_config(config_dir: Path = CONFIG_DIR) -> dict:
    """Get configuration from config file"""
    if not (config_dir / CONFIG_FILE_NAME).exists():
        return {}

    with open(config_dir / CONFIG_FILE_NAME) as f:
        return yaml.safe_load(f) or {}

def get_julep_yaml(source: Path) -> dict:
    """Get the julep.yaml file from the source directory"""

    if not (source / "julep.yaml").exists():
        typer.echo("Error: julep.yaml not found in source directory", err=True)
        raise typer.Exit(1)

    with open(source / "julep.yaml") as f:
        return yaml.safe_load(f)

def save_config(config: dict, config_dir: Path = CONFIG_DIR):
    """Save configuration to config file"""
    config_dir.mkdir(parents=True, exist_ok=True)

    with open(config_dir / CONFIG_FILE_NAME, "w") as f:
        yaml.dump(config, f)


def get_julep_client():
    """Get a Julep client"""
    # Initialize the Julep client
    api_key = get_config().get("api_key")
    if not api_key:
        typer.echo("Error: JULEP_API_KEY not set in config.yml", err=True)
        raise typer.Exit(1)

    # Get environment from config.yml or default to production
    environment = get_config().get("environment")

    if not environment:
        typer.echo("ENVIRONMENT not set in config.yml, defaulting to production")
        environment = "production"

    client = Julep(api_key=api_key, environment=environment)

    return client


def create_lock_file(source: Path):
    lock_file = source / "julep-lock.json"
    if not lock_file.exists():
        lock_file.touch()
        
        return lock_file
    else:
        typer.echo("julep-lock.json already exists in source directory", err=True)
        raise typer.Exit(1)


def get_lock_file(source: Path):
    lock_file = source / "julep-lock.json"

    if not lock_file.exists():
        typer.echo(
            "Error: julep-lock.json not found in source directory", err=True)
        raise typer.Exit(1)

    lock_file_contents = lock_file.read_text()

    return json.loads(lock_file_contents)


def fetch_all_remote_agents(client: Julep) -> list[CreateAgentRequest]:
    """Fetch all agents from the Julep platform"""
    i = 0
    agents: list[CreateAgentRequest] = []
    while True:
        new_agents = client.agents.list(limit=100, offset=i).items
        if len(new_agents) == 0:
            break
        
        for agent in new_agents:
            agents.append(CreateAgentRequest(**agent.model_dump(exclude_none=True, exclude_unset=True)))
        i += 100

    return agents

def fetch_all_local_agents(source: Path) -> list[tuple[CreateAgentRequest, Path]]:
    """Fetch all agents from the local source directory based on the julep.yaml file"""
    
    local_agents: list[tuple[CreateAgentRequest, Path]] = []

    julep_yaml_content = get_julep_yaml(source)
    agents = julep_yaml_content.get("agents", [])

    for agent in agents:
        agent_path = source / agent.pop("definition")
        local_agents.append((CreateAgentRequest(
            **yaml.safe_load(agent_path.read_text()), **agent), agent_path))

    return local_agents

def write_lock_file(lock_file: Path, content: LockFileContents):
    lock_file_contents = content.model_dump_json(indent=2)
    lock_file.write_text(lock_file_contents)
