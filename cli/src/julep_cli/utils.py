import json
from pathlib import Path

import typer
import yaml
from julep import Julep

import sqlite3
from typing import Callable, Any, Optional

from .models import (
    CreateAgentRequest,
    LockedEntity,
    LockFileContents,
    TaskAgentRelationship,
    ToolAgentRelationship,
)

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
        typer.echo("Error: julep.yaml not found in source directory")
        raise typer.Exit(1)

    with open(source / "julep.yaml") as f:
        return yaml.safe_load(f)


def write_julep_yaml(source: Path, julep_yaml_contents: dict):
    """Write the julep.yaml file"""

    with open(source / "julep.yaml", "w") as f:
        yaml.dump(julep_yaml_contents, f)


def save_config(config: dict, config_dir: Path = CONFIG_DIR):
    """Save configuration to config file"""
    config_dir.mkdir(parents=True, exist_ok=True)

    with open(config_dir / CONFIG_FILE_NAME, "w") as f:
        yaml.dump(config, f)


def get_julep_client() -> Julep:
    """Get a Julep client"""
    # Initialize the Julep client
    api_key = get_config().get("api_key")
    if not api_key:
        typer.echo("Error: JULEP_API_KEY not set in config.yml")
        raise typer.Exit(1)

    # Get environment from config.yml or default to production
    environment = get_config().get("environment")

    if not environment:
        typer.echo("ENVIRONMENT not set in config.yml, defaulting to production")
        environment = "production"

    return Julep(api_key=api_key, environment=environment, max_retries=0)


def create_lock_file(source: Path):
    lock_file = source / "julep-lock.json"
    if not lock_file.exists():
        lock_file.touch()

        return lock_file
    typer.echo("julep-lock.json already exists in source directory")
    raise typer.Exit(1)


def get_lock_file(project_dir: Path = Path.cwd()) -> LockFileContents:
    """
    Get the lock file from the project directory.
    If no project directory is provided, it will default to the current working directory.
    """

    lock_file = project_dir / "julep-lock.json"

    if not lock_file.exists():
        typer.echo("Error: julep-lock.json not found in source directory")
        raise typer.Exit(1)

    lock_file_contents = lock_file.read_text()

    return LockFileContents(**json.loads(lock_file_contents))


def fetch_all_remote_agents(client: Julep) -> list[CreateAgentRequest]:
    """Fetch all agents from the Julep platform"""
    i = 0
    agents: list[CreateAgentRequest] = []
    while True:
        new_agents = client.agents.list(limit=100, offset=i).items
        if len(new_agents) == 0:
            break

        agents.extend(
            CreateAgentRequest(**agent.model_dump(exclude_none=True, exclude_unset=True))
            for agent in new_agents
        )
        i += 100

    return agents


def fetch_all_local_agents(source: Path) -> list[tuple[CreateAgentRequest, Path]]:
    """Fetch all agents from the local source directory based on the julep.yaml file"""

    local_agents: list[tuple[CreateAgentRequest, Path]] = []

    julep_yaml_content = get_julep_yaml(source)
    agents = julep_yaml_content.get("agents", [])

    for agent in agents:
        agent_path = source / agent.pop("definition")
        local_agents.append((
            CreateAgentRequest(**yaml.safe_load(agent_path.read_text()), **agent),
            agent_path,
        ))

    return local_agents


def write_lock_file(project_dir: Path, content: LockFileContents):
    lock_file_path = project_dir / "julep-lock.json"
    lock_file_contents = content.model_dump_json(indent=2)
    lock_file_path.write_text(lock_file_contents)


def get_entity_from_lock_file(
    type: str, id: str, project_dir: Path = Path.cwd()
) -> LockedEntity:
    """
    Get the contents of lock file
    """

    lock_file = get_lock_file(project_dir)

    # Adding an s to match the plural form of the key in lock file (agent -> agents)
    entities: list[LockedEntity] = getattr(lock_file, type + "s", [])

    matched = [entity for entity in entities if entity.id == id]

    if len(matched) > 1:
        typer.echo(f"Error: Multiple {type}s with id '{id}' found in lock file")
        raise typer.Exit(1)

    if not matched:
        return None

    return matched[0]


def update_existing_entity_in_lock_file(
    type: str, new_entity: LockedEntity, project_dir: Path = Path.cwd()
):
    found = False
    lock_file = get_lock_file(project_dir)
    entities: list[LockedEntity] = getattr(lock_file, type + "s", [])

    for i in range(len(entities)):
        if entities[i].id == new_entity.id:
            entities[i] = new_entity
            found = True
            break

    if not found:
        typer.echo(
            f"Error: Cannot update{type} with id '{new_entity.get('id')}' because it was not found in lock file",
            err=True,
        )
        raise typer.Exit(1)

    setattr(lock_file, type + "s", entities)

    write_lock_file(project_dir, lock_file)


def add_entity_to_lock_file(
    type: str, new_entity: LockedEntity, project_dir: Path = Path.cwd()
):
    """
    Add a new entity to the lock file
    """

    lock_file = get_lock_file(project_dir)
    entities: list[LockedEntity] = getattr(lock_file, type + "s", [])

    entities.append(new_entity)

    setattr(lock_file, type + "s", entities)

    write_lock_file(project_dir, lock_file)


def update_yaml_for_existing_entity(path: Path, data: dict):
    """Update the yaml file for an existing entity"""
    with open(path, "w") as f:
        yaml.dump(data, f)


def add_agent_to_julep_yaml(source: Path, agent_data: dict):
    """Add a new entity to the julep.yaml file"""

    julep_yaml_contents = get_julep_yaml(source)

    julep_yaml_contents["agents"].append(agent_data)

    write_julep_yaml(source, julep_yaml_contents)


def get_related_agent_id(
    id: str, relationships_list: list[TaskAgentRelationship] | list[ToolAgentRelationship]
):
    for relationship in relationships_list:
        if relationship.id == id:
            return relationship.agent_id

    return None

# NEW DATABASE FUNCTIONS & DECORATOR FOR PERSISTING ATTRIBUTES

# Path to the SQLite database file in the Julep config directory
STATE_DB_PATH = CONFIG_DIR / "julep_state.db"

def get_state_db_connection() -> sqlite3.Connection:
    """
    Get a SQLite connection to the state database.
    This creates the CONFIG_DIR if it doesn't exist.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(STATE_DB_PATH))
    return conn

def init_state_db():
    """
    Initialize the state database with the 'attributes' table if it does not exist.
    The table stores key-value pairs, with the key as a unique identifier.
    """
    conn = get_state_db_connection()
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS attributes (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
    conn.close()

def persist_attribute(key: str, extractor: Optional[Callable[[Any], Any]] = None):
    """
    A decorator that persists an attribute from a function's return value
    into a SQLite database located in the ~/.config/julep/ directory.

    Parameters:
      key (str): The name of the attribute to store (e.g., "execution_id").
      extractor (Callable[[Any], Any], optional): A function that extracts the value from
          the function's return value. If not provided, the decorator will attempt to extract:
            - If the return value is a dict and contains 'key', it uses that.
            - Otherwise, if the return value has an attribute with the name 'key', it uses that.

    Usage Example:
      @persist_attribute("execution_id", extractor=lambda execution: execution.id)
      def create_execution(client, task_id, input_data):
          return client.executions.create(task_id=task_id, input=input_data)
    
    The attribute is stored as a string in the 'attributes' table.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            value = None
            if extractor is not None:
                value = extractor(result)
            else:
                # Attempt default extraction
                if isinstance(result, dict) and key in result:
                    value = result[key]
                elif hasattr(result, key):
                    value = getattr(result, key)

            if value is not None:
                init_state_db()  # Ensure the database and table exist
                conn = get_state_db_connection()
                with conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO attributes (key, value) VALUES (?, ?)",
                        (key, str(value))
                    )
                conn.close()
            return result
        return wrapper
    return decorator

# NEW FUNCTION TO FETCH/UPDATE ATTRIBUTE VALUES FROM/TO DATABASE
def manage_db_attribute(key: str, current_value: Optional[str] = None) -> str:
    """
    If current_value is None, fetch the attribute from the SQLite state database.
    If a value is provided, update the database with that value.

    Returns the fetched or provided value.
    """
    init_state_db()  # Ensure DB and table are initialized
    conn = get_state_db_connection()
    cursor = conn.cursor()

    if current_value is None:
        # Fetch value from the database
        cursor.execute("SELECT value FROM attributes WHERE key=?", (key,))
        row = cursor.fetchone()
        if row:
            value = row[0]
        else:
            typer.echo(f"[bold red]Error: No saved value for '{key}' found in the database, please provide one.[/bold red]", err=True)
            conn.close()
            raise typer.Exit(1)
    else:
        # Update the database with the provided value
        cursor.execute("INSERT OR REPLACE INTO attributes (key, value) VALUES (?, ?)", (key, current_value))
        conn.commit()
        value = current_value
    conn.close()
    return value
