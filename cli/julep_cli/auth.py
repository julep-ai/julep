import os
from pathlib import Path
from typing import Annotated

import typer
import yaml
from environs import Env

from .app import app

# Config handling
env = Env()
CONFIG_DIR = Path.home() / ".config" / "julep"
CONFIG_FILE_NAME = "config.yml"


def get_config(config_dir: Path = CONFIG_DIR):
    """Get configuration from config file"""
    if not (config_dir / CONFIG_FILE_NAME).exists():
        return {}

    with open(config_dir / CONFIG_FILE_NAME) as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict, config_dir: Path = CONFIG_DIR):
    """Save configuration to config file"""
    config_dir.mkdir(parents=True, exist_ok=True)

    with open(config_dir / CONFIG_FILE_NAME, "w") as f:
        yaml.dump(config, f)


@app.command()
def auth(
    api_key: Annotated[
        str | None,
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
